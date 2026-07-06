"""
Prompt Output Scorers
=====================

Deterministic, LLM-free metrics for grading a generated answer. Keeping the
scorers heuristic means the eval harness runs offline, for free, and gives the
*same* number every time - which is exactly what you want when comparing prompt
variants (no judge-model noise confounding the signal).

Every scorer returns a float in ``[0.0, 1.0]`` where higher is better, so they
can be averaged into a single comparable score per variant.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def strip_reasoning(answer: str) -> str:
    """Remove a chain-of-thought <thinking>...</thinking> block if present."""
    return re.sub(r"<thinking>.*?</thinking>", "", answer, flags=re.S | re.I).strip()


def citation_score(answer: str, source_names: Iterable[str]) -> float:
    """1.0 if the answer references at least one real source file, else 0.0."""
    lowered = answer.lower()
    for name in source_names:
        # Match the file name or its stem (without extension).
        stem = name.rsplit(".", 1)[0].lower()
        if name.lower() in lowered or (len(stem) > 3 and stem in lowered):
            return 1.0
    # Fall back to detecting a SOURCES section that names any .md file.
    if re.search(r"\b[\w\-]+\.md\b", lowered):
        return 1.0
    return 0.0


def format_adherence_score(answer: str) -> float:
    """
    Reward the expected ANSWER / SOURCES structure.

    Half credit for each section present - a graded signal that surfaces
    partial format drift instead of a brittle pass/fail.
    """
    score = 0.0
    if re.search(r"\banswer\s*:", answer, re.I):
        score += 0.5
    if re.search(r"\bsources?\s*:", answer, re.I):
        score += 0.5
    return score


def grounding_score(answer: str, context: str) -> float:
    """
    Fraction of the answer's content words that also appear in the context.

    A proxy for faithfulness: an answer invented out of thin air shares few
    tokens with the retrieved context. Stopwords are ignored so the metric
    reflects substantive overlap, not filler.
    """
    answer_tokens = _tokens(strip_reasoning(answer)) - _STOPWORDS
    if not answer_tokens:
        return 0.0
    context_tokens = _tokens(context)
    overlap = answer_tokens & context_tokens
    return len(overlap) / len(answer_tokens)


def keyword_recall_score(answer: str, expected_keywords: List[str]) -> float:
    """Fraction of expected key concepts the answer actually mentions."""
    if not expected_keywords:
        return 1.0
    lowered = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in lowered)
    return hits / len(expected_keywords)


def refusal_score(answer: str) -> float:
    """
    1.0 when the answer appropriately signals "not enough information".

    Used for the negative/out-of-scope test cases where the *correct* behavior
    is to decline rather than hallucinate.
    """
    refusal_markers = [
        "insufficient", "not contain", "no relevant", "cannot answer",
        "don't have", "do not have", "not enough", "unable to", "not covered",
        "not provided", "no information",
    ]
    lowered = answer.lower()
    return 1.0 if any(m in lowered for m in refusal_markers) else 0.0


# A small English + domain stopword set so grounding measures real overlap.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "for", "to", "of",
    "in", "on", "at", "by", "with", "as", "is", "are", "be", "you", "your",
    "it", "this", "that", "these", "those", "can", "should", "would", "will",
    "use", "using", "answer", "sources", "source", "content", "question",
    "context", "please", "when", "how", "what", "which", "from", "into",
}


def aggregate(scores: Dict[str, float], weights: Dict[str, float] | None = None) -> float:
    """Weighted mean of a metric dict, defaulting to equal weights."""
    if not scores:
        return 0.0
    if weights is None:
        return sum(scores.values()) / len(scores)
    total_w = sum(weights.get(k, 1.0) for k in scores)
    return sum(v * weights.get(k, 1.0) for k, v in scores.items()) / total_w


__all__ = [
    "citation_score",
    "format_adherence_score",
    "grounding_score",
    "keyword_recall_score",
    "refusal_score",
    "strip_reasoning",
    "aggregate",
]
