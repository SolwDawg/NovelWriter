"""CLI for the OpenRouter live V0 benchmark."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import time

from .contracts import EvalCase, EvalRunResult, StoryRun, StoryState, SystemVariant
from .eval_runner import load_cases
from .live_engine import LiveStoryEngine
from .live_openrouter import OpenRouterConfig, OpenRouterProvider, OpenRouterRequestError
from .metrics import aggregate_metrics, evaluate_case


def execute_live_case(
    case: EvalCase, system: SystemVariant, engine: LiveStoryEngine
) -> tuple[EvalRunResult, object]:
    started = time.perf_counter()
    try:
        run = engine.generate(case, system)
    except Exception as error:  # keep a suite run alive after provider failure
        run = StoryRun(
            variant=system,
            documents=[],
            final_state=StoryState(),
            extracted_event_ids=[],
            committed_scene_ids=[],
            schema_valid=False,
            validation_errors=[_safe_error_summary(error)],
            notes=[_safe_error_summary(error)],
        )
    run.latency_ms = (time.perf_counter() - started) * 1000
    result = EvalRunResult(
        case_id=case.id,
        variant=system,
        metrics=evaluate_case(case, run),
        notes=tuple(run.notes),
    )
    return result, run


def _safe_error_summary(error: Exception) -> str:
    """Keep provider diagnostics useful without persisting prompt/response text."""

    if isinstance(error, OpenRouterRequestError):
        return str(error)
    return f"{type(error).__name__} during live capability execution"


def write_live_suite(
    cases: list[EvalCase],
    systems: list[SystemVariant],
    output_dir: str | Path,
    env_file: str | Path,
    *,
    batch_size: int = 1,
    pause_seconds: float = 0.0,
    max_attempts: int = 3,
    resume: bool = False,
) -> list[EvalRunResult]:
    """Run live jobs in resumable batches.

    A job is retried only for transient provider failures, especially HTTP 429.
    Semantic validation failures remain recorded as benchmark results instead
    of being retried indefinitely.
    """

    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    if pause_seconds < 0:
        raise ValueError("pause_seconds must be >= 0")
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    output_path = Path(output_dir)
    stories_path = output_path / "stories"
    review_path = output_path / "human-review"
    progress_path = output_path / "progress.jsonl"
    stories_path.mkdir(parents=True, exist_ok=True)
    review_path.mkdir(parents=True, exist_ok=True)
    engine = LiveStoryEngine(OpenRouterProvider(OpenRouterConfig.from_environment(env_file)))
    job_order = [(case, system) for case in cases for system in systems]
    latest = _load_progress(progress_path) if resume else {}
    if not resume:
        progress_path.write_text("", encoding="utf-8")
    candidate_files: dict[tuple[str, SystemVariant], str] = {}
    for job_number, (case, system) in enumerate(job_order, start=1):
        candidate_files[(case.id, system)] = (
            f"{case.id}--candidate-{job_number:04d}.txt"
        )

    with progress_path.open("a", encoding="utf-8") as progress_handle:
        for batch_start in range(0, len(cases), batch_size):
            batch_cases = cases[batch_start : batch_start + batch_size]
            for case in batch_cases:
                for system in systems:
                    job_key = _job_key(case.id, system)
                    previous = latest.get(job_key)
                    if previous and _progress_is_finished(previous, max_attempts):
                        print(
                            f"[skip] {case.id} {system.value} "
                            f"attempt={previous.get('attempt', 0)}",
                            flush=True,
                        )
                        continue
                    attempt = int(previous.get("attempt", 0)) if previous else 0
                    while attempt < max_attempts:
                        attempt += 1
                        print(
                            f"[run] {case.id} {system.value} "
                            f"attempt={attempt}/{max_attempts}",
                            flush=True,
                        )
                        result, run = execute_live_case(case, system, engine)
                        story_file = stories_path / f"{case.id}--{system.value}.txt"
                        story_file.write_text(run.full_text, encoding="utf-8")
                        blind_file = review_path / candidate_files[(case.id, system)]
                        blind_file.write_text(run.full_text, encoding="utf-8")
                        enriched = EvalRunResult(
                            case_id=result.case_id,
                            variant=result.variant,
                            metrics=result.metrics,
                            story_path=str(story_file),
                            notes=result.notes,
                        )
                        record = {
                            **enriched.to_dict(),
                            "attempt": attempt,
                            "retryable": _is_retryable_result(enriched),
                        }
                        progress_handle.write(
                            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                        )
                        progress_handle.flush()
                        latest[job_key] = record
                        if not record["retryable"] or attempt >= max_attempts:
                            break
                        retry_wait = max(
                            pause_seconds,
                            _retry_after_from_notes(enriched.notes),
                        )
                        print(
                            f"[wait] {case.id} {system.value} "
                            f"retry_in={retry_wait:.0f}s",
                            flush=True,
                        )
                        _sleep_with_progress(retry_wait)
            if batch_start + batch_size < len(cases):
                _sleep_with_progress(pause_seconds)

    results = [
        _result_from_progress(latest[_job_key(case.id, system)])
        for case, system in job_order
        if _job_key(case.id, system) in latest
    ]
    rows: list[dict[str, object]] = []
    for result in results:
        rows.append(
            {
                "case_id": result.case_id,
                "variant": result.variant.value,
                **{
                    key: value
                    for key, value in result.metrics.items()
                    if not isinstance(value, dict)
                },
            }
        )
    output_path.mkdir(parents=True, exist_ok=True)
    with (output_path / "summary.jsonl").open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    fieldnames = sorted({key for row in rows for key in row})
    with (output_path / "summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    (review_path / "README.md").write_text(
        "# Blind live-model review\n\n"
        "Candidate numbers are intentionally not system names. Score the six V0 "
        "rubric dimensions and record an overall preferred candidate.\n",
        encoding="utf-8",
    )
    available_files = {
        (result.case_id, result.variant): candidate_files[(result.case_id, result.variant)]
        for result in results
        if result.metrics.get("schema_valid") and result.metrics.get("word_count", 0) > 0
    }
    _write_review_form(review_path, cases, systems, available_files)
    aggregates = {
        system.value: aggregate_metrics(
            [result.metrics for result in results if result.variant is system]
        )
        for system in systems
    }
    (output_path / "aggregate.json").write_text(
        json.dumps(aggregates, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    return results


def _job_key(case_id: str, system: SystemVariant) -> str:
    return f"{case_id}|{system.value}"


def _load_progress(path: Path) -> dict[str, dict[str, object]]:
    latest: dict[str, dict[str, object]] = {}
    if not path.exists():
        return latest
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        latest[_job_key(str(record["case_id"]), SystemVariant(record["variant"]))] = record
    return latest


def _progress_is_finished(record: dict[str, object], max_attempts: int) -> bool:
    return bool(record.get("metrics", {}).get("schema_valid")) or int(
        record.get("attempt", 0)
    ) >= max_attempts


def _result_from_progress(record: dict[str, object]) -> EvalRunResult:
    return EvalRunResult(
        case_id=str(record["case_id"]),
        variant=SystemVariant(str(record["variant"])),
        metrics=dict(record.get("metrics", {})),
        story_path=str(record["story_path"]) if record.get("story_path") else None,
        notes=tuple(str(note) for note in record.get("notes", [])),
    )


def _is_retryable_result(result: EvalRunResult) -> bool:
    haystack = " ".join(result.notes).lower()
    return any(
        marker in haystack
        for marker in (
            "http 429",
            "network error",
            "timed out",
            "http 500",
            "http 502",
            "http 503",
            "http 504",
        )
    )


def _retry_after_from_notes(notes: tuple[str, ...]) -> float:
    for note in notes:
        match = re.search(r"retry_after=([0-9]+(?:\.[0-9]+)?)", note)
        if match:
            return float(match.group(1))
    return 0.0


def _sleep_with_progress(seconds: float) -> None:
    remaining = max(0.0, seconds)
    while remaining > 0:
        interval = min(60.0, remaining)
        time.sleep(interval)
        remaining -= interval
        if remaining > 0:
            print(f"[wait] batch_pause_remaining={remaining:.0f}s", flush=True)


def _write_review_form(
    review_path: Path,
    cases: list[EvalCase],
    systems: list[SystemVariant],
    candidate_files: dict[tuple[str, SystemVariant], str],
) -> None:
    """Create blind B-vs-C and B-vs-D pair rows for human scoring."""

    pairs: list[dict[str, str]] = []
    for case in cases:
        for structured in (SystemVariant.STRUCTURED_C, SystemVariant.STRUCTURED_QA_D):
            if SystemVariant.BASELINE_B not in systems or structured not in systems:
                continue
            baseline_file = candidate_files.get((case.id, SystemVariant.BASELINE_B))
            structured_file = candidate_files.get((case.id, structured))
            if not baseline_file or not structured_file:
                continue
            # Deterministic blind order; the system mapping is intentionally not
            # written to the human-facing CSV.
            seed = sum(ord(character) for character in f"{case.id}:{structured.value}")
            if seed % 2:
                candidate_a, candidate_b = structured_file, baseline_file
            else:
                candidate_a, candidate_b = baseline_file, structured_file
            pairs.append(
                {
                    "pair_id": f"{case.id}-{structured.value}",
                    "candidate_a_file": candidate_a,
                    "candidate_b_file": candidate_b,
                    "preferred_candidate": "",
                    "coherence_a": "",
                    "coherence_b": "",
                    "engagement_a": "",
                    "engagement_b": "",
                    "character_consistency_a": "",
                    "character_consistency_b": "",
                    "ending_a": "",
                    "ending_b": "",
                    "tts_readability_a": "",
                    "tts_readability_b": "",
                    "repetition_a": "",
                    "repetition_b": "",
                    "comments": "",
                }
            )
    fieldnames = list(pairs[0]) if pairs else ["pair_id", "candidate_a_file", "candidate_b_file"]
    with (review_path / "review-form.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pairs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path("F:/Son/tool/NovelWriter/env.txt"),
    )
    parser.add_argument("--cases", type=Path, default=None)
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--system", default="all", choices=["all", *(item.value for item in SystemVariant)])
    parser.add_argument("--output-dir", type=Path, default=Path("results/live-v0"))
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--pause-seconds", type=float, default=60.0)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    cases = load_cases(args.cases) if args.cases else load_cases()
    if args.case_id:
        cases = [case for case in cases if case.id == args.case_id]
        if not cases:
            parser.error(f"unknown case: {args.case_id}")
    if args.max_cases is not None:
        cases = cases[: max(0, args.max_cases)]
    systems = list(SystemVariant) if args.system == "all" else [SystemVariant(args.system)]
    results = write_live_suite(
        cases,
        systems,
        args.output_dir,
        args.env_file,
        batch_size=args.batch_size,
        pause_seconds=args.pause_seconds,
        max_attempts=args.max_attempts,
        resume=args.resume,
    )
    print(f"ran {len(results)} live evaluations; output={args.output_dir}")
    for system in systems:
        metrics = [result.metrics for result in results if result.variant is system]
        print(f"{system.value}: {json.dumps(aggregate_metrics(metrics), sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
