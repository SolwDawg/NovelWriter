"""CLI and programmatic runner for the V0 evaluation harness."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import time
from typing import Iterable

from .baselines import run_baseline
from .contracts import EvalCase, EvalRunResult, StoryRun, SystemVariant
from .metrics import aggregate_metrics, evaluate_case
from .structured_engine import run_structured


DEFAULT_CASES = Path(__file__).resolve().parents[2] / "cases" / "eval_cases.jsonl"


def load_cases(path: str | Path = DEFAULT_CASES) -> list[EvalCase]:
    cases: list[EvalCase] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                cases.append(EvalCase.from_dict(json.loads(line)))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                raise ValueError(f"invalid eval case at line {line_number}: {error}") from error
    if not cases:
        raise ValueError(f"no eval cases found in {path}")
    return cases


def execute_case(case: EvalCase, system: SystemVariant) -> tuple[EvalRunResult, StoryRun]:
    started = time.perf_counter()
    if system in {SystemVariant.BASELINE_A, SystemVariant.BASELINE_B}:
        run = run_baseline(case, system)
    else:
        run = run_structured(case, system)
    run.latency_ms = (time.perf_counter() - started) * 1000
    metrics = evaluate_case(case, run)
    return EvalRunResult(case_id=case.id, variant=system, metrics=metrics, notes=tuple(run.notes)), run


def run_case(case: EvalCase, system: SystemVariant) -> EvalRunResult:
    """Run one case, matching the public V0 harness interface."""

    result, _ = execute_case(case, system)
    return result


def _blind_id(case_id: str, variant: SystemVariant) -> str:
    digest = hashlib.sha256(f"{case_id}:{variant.value}".encode("utf-8")).hexdigest()
    return digest[:12]


def write_suite(
    cases: Iterable[EvalCase],
    systems: Iterable[SystemVariant],
    output_dir: str | Path,
) -> list[EvalRunResult]:
    output_path = Path(output_dir)
    stories_path = output_path / "stories"
    review_path = output_path / "human-review"
    output_path.mkdir(parents=True, exist_ok=True)
    stories_path.mkdir(parents=True, exist_ok=True)
    review_path.mkdir(parents=True, exist_ok=True)
    case_list = list(cases)
    system_list = list(systems)
    results: list[EvalRunResult] = []
    rows: list[dict[str, object]] = []

    for case in case_list:
        for system in system_list:
            result, run = execute_case(case, system)
            story_file = stories_path / f"{case.id}--{system.value}.txt"
            story_file.write_text(run.full_text, encoding="utf-8")
            blind_file = review_path / f"{case.id}--candidate-{_blind_id(case.id, system)}.txt"
            blind_file.write_text(run.full_text, encoding="utf-8")
            result = EvalRunResult(
                case_id=result.case_id,
                variant=result.variant,
                metrics=result.metrics,
                story_path=str(story_file),
                notes=result.notes,
            )
            results.append(result)
            rows.append(
                {
                    "case_id": result.case_id,
                    "variant": result.variant.value,
                    **{key: value for key, value in result.metrics.items() if not isinstance(value, dict)},
                }
            )

    with (output_path / "summary.jsonl").open("w", encoding="utf-8", newline="") as handle:
        for result in results:
            handle.write(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    fieldnames = sorted({key for row in rows for key in row})
    with (output_path / "summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    blind_readme = (
        "# Blind paired-review packet\n\n"
        "Candidate filenames intentionally use opaque IDs. Reviewers should score "
        "coherence, engagement, character consistency, ending satisfaction, TTS "
        "readability, and repetition without using the system names.\n"
    )
    (review_path / "README.md").write_text(blind_readme, encoding="utf-8")
    aggregates = {
        system.value: aggregate_metrics(
            [result.metrics for result in results if result.variant is system]
        )
        for system in system_list
    }
    (output_path / "aggregate.json").write_text(
        json.dumps(aggregates, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    return results


def _parse_system(value: str) -> list[SystemVariant]:
    if value == "all":
        return list(SystemVariant)
    return [SystemVariant(value)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--system", default="all", choices=["all", *(item.value for item in SystemVariant)])
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--output-dir", type=Path, default=Path("results/latest"))
    args = parser.parse_args(argv)

    cases = load_cases(args.cases)
    if args.case_id:
        cases = [case for case in cases if case.id == args.case_id]
        if not cases:
            parser.error(f"unknown case: {args.case_id}")
    results = write_suite(cases, _parse_system(args.system), args.output_dir)
    print(f"ran {len(results)} evaluations; output={args.output_dir}")
    for variant in _parse_system(args.system):
        variant_results = [result.metrics for result in results if result.variant is variant]
        print(f"{variant.value}: {json.dumps(aggregate_metrics(variant_results), sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

