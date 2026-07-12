"""
Versioned Prompt Library
========================

A single, auditable home for every prompt the RAG system uses.

Why this exists
---------------
Prompts are the "source code" of an LLM application. Treating them as
throwaway f-strings scattered across the codebase makes them impossible to
version, test, or improve systematically. This module instead treats each
prompt as a first-class, versioned artifact so we can:

    * A/B test variants against each other (see ``app/eval``)
    * Track *which technique* a variant uses (few-shot, chain-of-thought,
      structured output) and *why* it was chosen
    * Roll a prompt forward/back by referencing a stable ``(name, version)``

Prompt-engineering techniques demonstrated here
-----------------------------------------------
    * Zero-shot            - a direct instruction with role + constraints
    * Few-shot             - inline input/output exemplars to anchor format
    * Chain-of-thought     - an explicit private reasoning step before answering
    * Structured output    - a strict JSON contract for machine-parseable results

Each variant records its rationale so a reviewer can see the *intent* behind
the wording, not just the wording.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple


class Technique(str, Enum):
    """The prompt-engineering technique a template primarily relies on."""

    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    STRUCTURED_OUTPUT = "structured_output"


@dataclass(frozen=True)
class PromptTemplate:
    """
    An immutable, versioned prompt.

    Attributes
    ----------
    name:
        Stable identifier for the *task* (e.g. ``"rag_answer"``). Multiple
        versions share a name.
    version:
        Monotonically increasing integer. ``(name, version)`` is unique.
    technique:
        The primary technique this variant demonstrates.
    description:
        One-line human summary shown in eval reports.
    system:
        The system / instruction template. May contain ``{placeholders}``.
    user:
        The user-message template. May contain ``{placeholders}``.
    rationale:
        *Why* this variant is worded the way it is. This is the field a
        reviewer (or hiring manager) reads to understand the design intent.
    expects_json:
        True when the template asks the model for a strict JSON object, so
        callers know to parse rather than display the raw text.
    """

    name: str
    version: int
    technique: Technique
    description: str
    system: str
    user: str
    rationale: str = ""
    expects_json: bool = False

    @property
    def id(self) -> str:
        """Stable ``name@vN`` identifier used in logs and eval tables."""
        return f"{self.name}@v{self.version}"

    def render(self, **kwargs) -> Tuple[str, str]:
        """
        Fill placeholders and return ``(system, user)``.

        Missing placeholders raise ``KeyError`` loudly rather than silently
        producing a half-formed prompt - a common, hard-to-debug failure mode.
        """
        try:
            return self.system.format(**kwargs), self.user.format(**kwargs)
        except KeyError as missing:
            raise KeyError(
                f"Prompt {self.id!r} is missing template variable {missing}. "
                f"Provided: {sorted(kwargs)}"
            ) from None


# ---------------------------------------------------------------------------
# RAG ANSWER PROMPTS
#
# The core task: given retrieved context + a question, produce a grounded,
# cited answer. Three variants let us measure the payoff of each technique.
# ---------------------------------------------------------------------------

_RAG_V1_BASELINE = PromptTemplate(
    name="rag_answer",
    version=1,
    technique=Technique.ZERO_SHOT,
    description="Baseline zero-shot: role + grounding + citation constraints.",
    rationale=(
        "The control group. A clear role, an explicit 'only use the context' "
        "grounding rule, and a fixed output shape. Everything more elaborate "
        "is measured against this."
    ),
    system=(
        "You are a knowledgeable assistant for GreenScape Lawn & Landscape, "
        "helping employees answer customer questions.\n"
        "Answer the user's question using ONLY the provided context.\n"
        "If the context is insufficient, say so plainly instead of guessing.\n"
        "Always cite at least one source by its file name.\n\n"
        "Format your reply exactly as:\n"
        "ANSWER:\n<your answer>\n\n"
        "SOURCES:\n- <source file name>"
    ),
    user="Context:\n{context}\n\nQuestion: {query}",
)

_RAG_V2_FEW_SHOT = PromptTemplate(
    name="rag_answer",
    version=2,
    technique=Technique.FEW_SHOT,
    description="Few-shot: one exemplar anchors tone, grounding, and citation.",
    rationale=(
        "Adds a single worked example. Small models drift on format and forget "
        "to cite; one exemplar reliably locks the ANSWER/SOURCES shape and "
        "demonstrates the 'refuse when unsupported' behavior without a long "
        "rules list. Cheap on tokens, high on format adherence."
    ),
    system=(
        "You are a knowledgeable assistant for GreenScape Lawn & Landscape, "
        "helping employees answer customer questions.\n"
        "Answer using ONLY the provided context, and cite the source file(s).\n"
        "If the context does not contain the answer, say so.\n\n"
        "--- EXAMPLE ---\n"
        "Context:\n"
        "Source: fertilization_weed_control.md\n"
        "Content: After a treatment, keep kids and pets off the lawn until it is "
        "fully dry, usually 1 to 2 hours.\n\n"
        "Question: How long until my lawn is safe for pets after a treatment?\n\n"
        "ANSWER:\n"
        "Keep pets and kids off the lawn until the treatment is fully dry, which "
        "usually takes about 1 to 2 hours.\n\n"
        "SOURCES:\n- fertilization_weed_control.md\n"
        "--- END EXAMPLE ---"
    ),
    user="Context:\n{context}\n\nQuestion: {query}\n\nANSWER:",
)

_RAG_V3_COT = PromptTemplate(
    name="rag_answer",
    version=3,
    technique=Technique.CHAIN_OF_THOUGHT,
    description="Chain-of-thought: private reasoning step, then a clean answer.",
    rationale=(
        "For multi-part or comparison questions, quality improves when the "
        "model first checks the context against the question privately. We keep "
        "the scratchpad OUT of the user-facing answer to avoid leaking verbose "
        "reasoning - a practical structured-CoT pattern."
    ),
    system=(
        "You are a knowledgeable assistant for GreenScape Lawn & Landscape, "
        "helping employees answer customer questions.\n"
        "Work in two steps.\n"
        "STEP 1 (private): In a <thinking> block, list which pieces of the "
        "context are relevant and whether they fully answer the question.\n"
        "STEP 2 (public): Write the final answer using ONLY supported facts, "
        "and cite the source file(s). If support is missing, say so.\n\n"
        "Output format:\n"
        "<thinking>\n<your private reasoning>\n</thinking>\n"
        "ANSWER:\n<final answer>\n\n"
        "SOURCES:\n- <source file name>"
    ),
    user="Context:\n{context}\n\nQuestion: {query}",
)


# ---------------------------------------------------------------------------
# DOCUMENT ANALYSIS PROMPTS
#
# Task: summarize a chunk and emit machine-readable metadata. The v2 variant
# demonstrates a strict JSON contract (structured output / function-calling
# friendly) vs. the v1 delimiter-parsed text.
# ---------------------------------------------------------------------------

_ANALYZE_V1_DELIMITED = PromptTemplate(
    name="analyze_document",
    version=1,
    technique=Technique.ZERO_SHOT,
    description="Delimiter-parsed sections (SUMMARY / TAGS / COMPLEXITY).",
    rationale=(
        "Works on tiny local models that cannot reliably emit JSON. The trade-off "
        "is brittle string parsing on our side."
    ),
    system="",
    user=(
        "Analyze this text and provide:\n"
        "1. A concise summary (2-3 sentences)\n"
        "2. 3-5 relevant topic tags\n"
        "3. Complexity level (beginner/intermediate/advanced)\n\n"
        "Text:\n{text}\n\n"
        "Respond in this exact format:\n\n"
        "SUMMARY:\n<summary>\n\n"
        "TAGS:\n<tag1>, <tag2>, <tag3>\n\n"
        "COMPLEXITY:\n<beginner/intermediate/advanced>"
    ),
)

_ANALYZE_V2_JSON = PromptTemplate(
    name="analyze_document",
    version=2,
    technique=Technique.STRUCTURED_OUTPUT,
    description="Strict JSON object - parseable, schema-validated downstream.",
    expects_json=True,
    rationale=(
        "Preferred on capable models (Gemini/GPT/Claude). A strict JSON schema "
        "removes fragile text parsing, makes outputs directly usable by other "
        "services, and pairs with the provider's JSON/function-calling mode. "
        "We pin enum values and array sizes to keep results predictable."
    ),
    system=(
        "You are a precise document-analysis engine. "
        "You reply with a single JSON object and nothing else - no prose, no "
        "code fences."
    ),
    user=(
        "Analyze the text below and return JSON matching exactly this schema:\n"
        "{{\n"
        '  "summary": string,            // 2-3 sentences\n'
        '  "tags": string[],             // 3-5 lowercase topic tags\n'
        '  "complexity": string          // one of: "beginner","intermediate","advanced"\n'
        "}}\n\n"
        "Text:\n{text}"
    ),
)


# ---------------------------------------------------------------------------
# FOLLOW-UP QUESTION PROMPT
# ---------------------------------------------------------------------------

_FOLLOWUP_V1 = PromptTemplate(
    name="follow_up",
    version=1,
    technique=Technique.ZERO_SHOT,
    description="Generate three related follow-up questions.",
    rationale=(
        "Constrained to exactly three, one per line, exploring gaps the answer "
        "did not cover - keeps the UI's question chips consistent and parseable."
    ),
    system="",
    user=(
        "Given this question and answer, generate exactly 3 follow-up "
        "questions that explore related aspects NOT already covered.\n"
        "Rules: one question per line, each ends with '?', no numbering.\n\n"
        "Question: {query}\n"
        "Answer: {answer}\n\n"
        "Follow-up questions:"
    ),
)


class PromptRegistry:
    """
    In-memory registry of every prompt variant.

    Lookups default to the highest version for a name (the "production"
    prompt), while the eval harness can enumerate *all* versions to compare.
    """

    def __init__(self, templates: List[PromptTemplate]):
        self._by_name: Dict[str, Dict[int, PromptTemplate]] = {}
        for t in templates:
            self._by_name.setdefault(t.name, {})[t.version] = t

    def get(self, name: str, version: int | None = None) -> PromptTemplate:
        """Return a specific version, or the latest when ``version`` is None."""
        if name not in self._by_name:
            raise KeyError(f"No prompt registered under {name!r}")
        versions = self._by_name[name]
        if version is None:
            version = max(versions)
        if version not in versions:
            raise KeyError(
                f"Prompt {name!r} has no version {version}. "
                f"Available: {sorted(versions)}"
            )
        return versions[version]

    def variants(self, name: str) -> List[PromptTemplate]:
        """All versions of a prompt, ascending - used for A/B evaluation."""
        if name not in self._by_name:
            raise KeyError(f"No prompt registered under {name!r}")
        return [self._by_name[name][v] for v in sorted(self._by_name[name])]

    def names(self) -> List[str]:
        return sorted(self._by_name)


# The single shared registry. Import this everywhere instead of hard-coding
# prompt strings.
REGISTRY = PromptRegistry(
    [
        _RAG_V1_BASELINE,
        _RAG_V2_FEW_SHOT,
        _RAG_V3_COT,
        _ANALYZE_V1_DELIMITED,
        _ANALYZE_V2_JSON,
        _FOLLOWUP_V1,
    ]
)

__all__ = ["Technique", "PromptTemplate", "PromptRegistry", "REGISTRY"]
