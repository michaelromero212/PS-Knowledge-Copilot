"""
Prompt A/B Evaluation Runner
============================

Runs every registered variant of a prompt against the golden dataset, scores
each answer with the deterministic scorers, and prints a side-by-side
comparison table. This is the "iterative testing & analysis" loop: change a
prompt, re-run, watch the numbers move.

Usage
-----
    # Offline demo (no API key, deterministic mock generator):
    python -m app.eval.runner

    # Against a live provider:
    python -m app.eval.runner --provider gemini
    python -m app.eval.runner --provider huggingface_local

Injection cases are graded on the *guardrail* (did we block it?), not the model
output - because a well-designed system never sends those to the LLM at all.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Dict, List

from app.eval import scorers
from app.eval.dataset import GOLDEN_CASES, EvalCase
from app.prompts.guardrails import check_user_input
from app.prompts.library import REGISTRY, PromptTemplate

# A generator turns (system_prompt, user_prompt) into a model response string.
Generator = Callable[[str, str], str]


@dataclass
class CaseResult:
    case_id: str
    intent: str
    metrics: Dict[str, float]
    overall: float
    answer_preview: str


@dataclass
class VariantReport:
    prompt_id: str
    technique: str
    description: str
    mean_score: float
    case_results: List[CaseResult] = field(default_factory=list)
    guardrail_block_rate: float = 0.0


def _score_generated(case: EvalCase, answer: str) -> Dict[str, float]:
    """Score a normal (grounded/refusal) case based on its intent."""
    source_names = [
        line.split("Source:")[1].strip()
        for line in case.stub_context.splitlines()
        if line.strip().startswith("Source:")
    ]
    if case.intent == "refusal":
        # Reward declining; grounding still matters so it doesn't invent facts.
        return {
            "refusal": scorers.refusal_score(answer),
            "grounding": scorers.grounding_score(answer, case.stub_context),
        }
    # grounded
    return {
        "citation": scorers.citation_score(answer, source_names),
        "format": scorers.format_adherence_score(answer),
        "grounding": scorers.grounding_score(answer, case.stub_context),
        "keyword_recall": scorers.keyword_recall_score(answer, case.expected_keywords),
    }


def evaluate_variant(variant: PromptTemplate, generate: Generator) -> VariantReport:
    """Run one prompt variant across all golden cases."""
    case_results: List[CaseResult] = []
    injection_total = 0
    injection_blocked = 0

    for case in GOLDEN_CASES:
        if case.intent == "injection":
            injection_total += 1
            guard = check_user_input(case.query)
            blocked = guard.blocked
            injection_blocked += int(blocked)
            case_results.append(
                CaseResult(
                    case_id=case.id,
                    intent=case.intent,
                    metrics={"blocked": 1.0 if blocked else 0.0},
                    overall=1.0 if blocked else 0.0,
                    answer_preview=f"guardrail={'BLOCKED' if blocked else 'ALLOWED'} "
                    f"({guard.reason or 'n/a'})",
                )
            )
            continue

        # Guardrail-sanitize the input, then render + generate.
        guard = check_user_input(case.query)
        system, user = variant.render(context=case.stub_context, query=guard.text)
        answer = generate(system, user)

        metrics = _score_generated(case, answer)
        overall = scorers.aggregate(metrics)
        case_results.append(
            CaseResult(
                case_id=case.id,
                intent=case.intent,
                metrics=metrics,
                overall=overall,
                answer_preview=scorers.strip_reasoning(answer)[:80].replace("\n", " "),
            )
        )

    graded = [c.overall for c in case_results if c.intent != "injection"]
    mean_score = sum(graded) / len(graded) if graded else 0.0
    block_rate = injection_blocked / injection_total if injection_total else 0.0

    return VariantReport(
        prompt_id=variant.id,
        technique=variant.technique.value,
        description=variant.description,
        mean_score=mean_score,
        case_results=case_results,
        guardrail_block_rate=block_rate,
    )


def run(prompt_name: str, generate: Generator) -> List[VariantReport]:
    """Evaluate every variant of ``prompt_name`` and return sorted reports."""
    reports = [evaluate_variant(v, generate) for v in REGISTRY.variants(prompt_name)]
    reports.sort(key=lambda r: r.mean_score, reverse=True)
    return reports


def print_report(reports: List[VariantReport]) -> None:
    """Pretty-print the leaderboard + per-case detail for the winner."""
    print("\n" + "=" * 72)
    print("PROMPT A/B EVALUATION  ·  ranked by mean grounded/refusal score")
    print("=" * 72)
    print(f"{'variant':<16}{'technique':<20}{'score':>8}{'guardrail':>12}")
    print("-" * 72)
    for r in reports:
        print(
            f"{r.prompt_id:<16}{r.technique:<20}"
            f"{r.mean_score:>8.3f}{r.guardrail_block_rate:>11.0%}"
        )

    winner = reports[0]
    print("\nWinner:", winner.prompt_id, "-", winner.description)
    print("-" * 72)
    print(f"{'case':<28}{'intent':<12}{'score':>7}   preview")
    print("-" * 72)
    for c in winner.case_results:
        print(f"{c.case_id:<28}{c.intent:<12}{c.overall:>7.2f}   {c.answer_preview}")
    print("=" * 72 + "\n")


# --------------------------------------------------------------------------- #
# Generators
# --------------------------------------------------------------------------- #

def mock_generator(system: str, user: str) -> str:
    """
    Deterministic offline generator so the harness runs with no API key.

    It echoes context sentences and emits the expected ANSWER/SOURCES shape,
    which lets us validate the *scorers* and pipeline end-to-end for free.
    """
    context = ""
    if "Context:" in user:
        context = user.split("Context:", 1)[1]
    context = context.split("Question:", 1)[0]

    # Pull the source name and first content sentence from the stub context.
    source = "unknown.md"
    content = ""
    for line in context.splitlines():
        line = line.strip()
        if line.startswith("Source:"):
            source = line.split("Source:", 1)[1].strip()
        elif line.startswith("Content:"):
            content = line.split("Content:", 1)[1].strip()
    first_sentence = content.split(".")[0].strip() if content else ""
    return f"ANSWER:\n{first_sentence}.\n\nSOURCES:\n- {source}"


def live_generator(provider: str, delay: float = 0.0, max_retries: int = 4) -> Generator:
    """
    Build a generator backed by a real LLMConnector provider.

    Adds rate-limit resilience: a fixed inter-call ``delay`` to stay under
    per-minute quotas, plus exponential backoff when the provider returns a
    429 / quota error. Without this, a burst of eval calls trips free-tier
    limits and later variants score artificially low - corrupting the A/B
    comparison.
    """
    from app.rag.llm_connector import LLMConnector

    connector = LLMConnector(provider=provider)

    def _is_rate_limited(text: str) -> bool:
        t = text.lower()
        return "429" in t or "quota" in t or "rate limit" in t

    def _generate(system: str, user: str) -> str:
        out = ""
        for attempt in range(max_retries):
            if delay:
                time.sleep(delay)
            out = connector._call_provider(system, user)
            if not (out.startswith("Error") and _is_rate_limited(out)):
                return out
            # Exponential backoff: 2s, 4s, 8s, ...
            backoff = 2 ** (attempt + 1)
            print(f"  rate limited; backing off {backoff}s "
                  f"(attempt {attempt + 1}/{max_retries})")
            time.sleep(backoff)
        return out

    return _generate


def main() -> None:
    # Load .env so live providers pick up their API keys when run standalone.
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="Prompt A/B evaluation harness.")
    parser.add_argument("--prompt", default="rag_answer", help="Prompt name to evaluate.")
    parser.add_argument(
        "--provider",
        default=None,
        help="LLM provider (e.g. gemini, huggingface_local). Omit for offline mock.",
    )
    parser.add_argument("--save", default=None, help="Optional path to write JSON results.")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to pause between live calls to respect rate limits "
        "(e.g. 5 for free-tier Gemini).",
    )
    args = parser.parse_args()

    generate = (
        live_generator(args.provider, delay=args.delay) if args.provider else mock_generator
    )
    mode = args.provider or "mock (offline)"
    print(f"\nEvaluating prompt {args.prompt!r} · generator: {mode}")

    start = time.time()
    reports = run(args.prompt, generate)
    print_report(reports)
    print(f"Completed in {time.time() - start:.1f}s")

    if args.save:
        Path(args.save).write_text(json.dumps([asdict(r) for r in reports], indent=2))
        print(f"Results written to {args.save}")


if __name__ == "__main__":
    main()
