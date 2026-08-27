"""Deterministic metrics for the V0 engine ablation."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from .contracts import EvalCase, SceneDocument, StoryRun


def _scene_index(scene_id: str) -> int | None:
    match = re.fullmatch(r"scene-(\d+)", scene_id)
    return int(match.group(1)) if match else None


def _document_for_scene(run: StoryRun, scene: int) -> SceneDocument | None:
    for document in run.documents:
        if _scene_index(document.scene_id) == scene:
            return document
    return None


def locked_canon_violations(case: EvalCase, run: StoryRun) -> list[str]:
    text = run.full_text.casefold()
    violations: list[str] = []
    for fact in case.canon_facts:
        if fact.locked and any(phrase.casefold() in text for phrase in fact.negative_phrases):
            violations.append(fact.id)
    return violations


def required_outcome_results(case: EvalCase, run: StoryRun) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for index, outcome in enumerate(case.required_outcomes, start=1):
        document = _document_for_scene(run, outcome.scene)
        haystack = (document.full_text if document else run.full_text).casefold()
        results[f"outcome_{index}"] = outcome.text.casefold() in haystack
    return results


def forbidden_reveal_violations(case: EvalCase, run: StoryRun) -> list[str]:
    violations: list[str] = []
    for reveal in case.forbidden_reveals:
        for document in run.documents:
            scene = _scene_index(document.scene_id)
            if scene is not None and scene >= reveal.before_scene:
                continue
            if reveal.text.casefold() in document.full_text.casefold():
                violations.append(reveal.text)
    return violations


def extractor_scores(case: EvalCase, run: StoryRun) -> tuple[float, float, float]:
    expected = {event.id for event in case.events}
    predicted = set(run.extracted_event_ids)
    true_positives = len(expected & predicted)
    precision = true_positives / len(predicted) if predicted else (1.0 if not expected else 0.0)
    recall = true_positives / len(expected) if expected else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return precision, recall, f1


def evaluate_case(case: EvalCase, run: StoryRun) -> dict[str, Any]:
    canon_violations = locked_canon_violations(case, run)
    outcome_results = required_outcome_results(case, run)
    outcome_rate = (
        sum(outcome_results.values()) / len(outcome_results) if outcome_results else 1.0
    )
    precision, recall, f1 = extractor_scores(case, run)
    forbidden = forbidden_reveal_violations(case, run)
    unresolved = [
        thread_id
        for thread_id in case.critical_threads
        if thread_id not in run.final_state.resolved_threads
    ]
    word_error = abs(run.word_count - case.target_words) / case.target_words
    return {
        "locked_canon_violations": len(canon_violations),
        "locked_canon_pass": not canon_violations,
        "forbidden_reveal_violations": len(forbidden),
        "schema_valid": run.schema_valid,
        "required_outcome_pass_rate": outcome_rate,
        "required_outcomes": outcome_results,
        "state_extractor_precision": precision,
        "state_extractor_recall": recall,
        "state_extractor_f1": f1,
        "unresolved_critical_threads": len(unresolved),
        "word_count": run.word_count,
        "target_words": case.target_words,
        "word_count_error_ratio": word_error,
        "committed_scene_count": len(run.committed_scene_ids),
        "input_tokens": run.usage.input_tokens,
        "output_tokens": run.usage.output_tokens,
        "estimated_cost_usd": run.usage.estimated_cost_usd,
        "latency_ms": run.latency_ms,
        "validation_error_count": len(run.validation_errors),
    }


def aggregate_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {}
    numeric_keys = (
        "required_outcome_pass_rate",
        "state_extractor_f1",
        "word_count_error_ratio",
        "estimated_cost_usd",
        "latency_ms",
        "committed_scene_count",
    )
    summary: dict[str, Any] = {"case_count": len(results)}
    for key in numeric_keys:
        summary[key] = sum(float(item[key]) for item in results) / len(results)
    summary["locked_canon_pass_rate"] = sum(
        bool(item["locked_canon_pass"]) for item in results
    ) / len(results)
    summary["schema_valid_rate"] = sum(bool(item["schema_valid"]) for item in results) / len(results)
    summary["forbidden_reveal_violation_count"] = sum(
        int(item["forbidden_reveal_violations"]) for item in results
    )
    summary["validation_error_count"] = sum(int(item["validation_error_count"]) for item in results)
    return summary

