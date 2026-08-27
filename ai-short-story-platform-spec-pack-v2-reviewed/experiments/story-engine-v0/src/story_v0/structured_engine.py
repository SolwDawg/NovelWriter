"""Dependency-free structured Story Engine used by the V0 proof.

This is a deterministic fixture implementation, not the production AI runtime.
It intentionally models the authority boundary that the production architecture
requires:

    Scene Writer -> SceneDocument
    State Extractor -> Proposed StoryStateDelta
    Domain validation -> accepted StoryState
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .baselines import (
    document_from_text,
    estimate_usage,
    make_outline,
    pad_to_target,
    scene_count_for_target,
)
from .contracts import (
    Blueprint,
    CanonFact,
    ContractValidationError,
    EvalCase,
    SceneBlock,
    SceneDocument,
    SceneEvent,
    ScenePlan,
    SceneWriterResult,
    StateChange,
    StoryRun,
    StoryState,
    StoryStateDelta,
    SystemVariant,
    Usage,
    ValidationResult,
)


class DomainConflictError(ValueError):
    """Raised when a state commit violates an authoritative invariant."""


@dataclass(frozen=True)
class CriticResult:
    passed: bool
    issues: tuple[str, ...] = ()


def _set_path(state: StoryState, path: str, value: Any) -> None:
    """Apply a JSON-friendly state path to the materialized projection."""

    parts = path.split(".")
    if len(parts) < 2:
        raise DomainConflictError(f"state path must contain a collection and key: {path}")
    collection_name, key = parts[0], ".".join(parts[1:])
    collection = getattr(state, collection_name, None)
    if not isinstance(collection, dict):
        raise DomainConflictError(f"unsupported state collection: {collection_name}")
    collection[key] = value


class StructuredStoryEngine:
    """Runs C/D against deterministic fixture cases."""

    def __init__(self, *, max_repair_attempts: int = 1) -> None:
        self.max_repair_attempts = max_repair_attempts

    def interpret_intent(self, case: EvalCase):
        from .contracts import Premise

        return Premise(
            raw_idea=case.premise,
            normalized_idea=case.premise.strip(),
            language=case.language,
            genre=case.genre,
            target_words=case.target_words,
        )

    def architect(self, case: EvalCase, premise) -> Blueprint:
        return make_outline(case)

    def plan_scenes(self, case: EvalCase, blueprint: Blueprint) -> list[ScenePlan]:
        scene_count = blueprint.scene_count or scene_count_for_target(case.target_words)
        base_words = case.target_words // scene_count
        remainder = case.target_words - (base_words * scene_count)
        events_by_scene: dict[int, list[SceneEvent]] = {}
        for event in case.events:
            events_by_scene.setdefault(event.scene, []).append(event)
        outcomes_by_scene: dict[int, list[str]] = {}
        for outcome in case.required_outcomes:
            outcomes_by_scene.setdefault(outcome.scene, []).append(outcome.text)

        plans: list[ScenePlan] = []
        for index in range(1, scene_count + 1):
            events = events_by_scene.get(index, [])
            outcomes = outcomes_by_scene.get(index, [])
            required = [event.text for event in events] + outcomes
            required = list(dict.fromkeys(required))
            purpose = (
                "thiết lập mâu thuẫn"
                if index == 1
                else "đẩy manh mối và lựa chọn tiến về phía hồi kết"
            )
            forbidden = [
                reveal.text
                for reveal in case.forbidden_reveals
                if index < reveal.before_scene
            ]
            plans.append(
                ScenePlan(
                    scene_id=f"scene-{index:03d}",
                    index=index,
                    purpose=purpose,
                    required_outcome="; ".join(required) or "một bước tiến mới xảy ra",
                    required_facts=tuple(required),
                    forbidden_reveals=tuple(forbidden),
                    active_threads=case.critical_threads,
                    target_tension=min(10, 3 + round((index / scene_count) * 7)),
                    target_words=base_words + (1 if index <= remainder else 0),
                    pov="ngôi thứ ba",
                    location="địa điểm được ghi trong StoryState",
                    participants=(),
                )
            )
        return plans

    def write_scene(
        self, case: EvalCase, plan: ScenePlan, state: StoryState
    ) -> SceneWriterResult:
        """Return only a document; never a StoryStateDelta."""

        paragraphs = [
            (
                f"Cảnh {plan.index} bắt đầu khi nhân vật quay lại với câu hỏi: "
                f"{case.premise}"
            ),
            (
                f"Mục đích của cảnh là {plan.purpose}. Nhịp căng thẳng được giữ ở "
                f"mức {plan.target_tension}/10."
            ),
        ]
        # The fixture writer expresses required facts in prose. It does not
        # return these facts as a delta; the extractor must recover them below.
        paragraphs.extend(f"Một sự kiện quan trọng được xác nhận: {fact}." for fact in plan.required_facts)
        if not plan.required_facts:
            paragraphs.append("Một manh mối mới xuất hiện nhưng chưa giải đáp toàn bộ bí ẩn.")
        paragraphs.append(
            "Nhân vật ghi nhớ những gì đã xảy ra và bước tiếp, để cảnh sau có thể "
            "kiểm tra hệ quả thay vì bắt đầu lại từ đầu."
        )
        text = pad_to_target("\n".join(paragraphs), plan.target_words, plan.scene_id)
        document = document_from_text(plan.scene_id, text)
        return SceneWriterResult(
            document=document,
            usage=estimate_usage(case.premise + plan.required_outcome, text),
            diagnostics=("fixture-writer", "no-authoritative-delta"),
        )

    def extract_state_delta(
        self,
        case: EvalCase,
        plan: ScenePlan,
        document: SceneDocument,
        state: StoryState,
    ) -> tuple[StoryStateDelta, Usage]:
        """Recover state transitions from accepted candidate prose."""

        text = document.full_text.casefold()
        changes: list[StateChange] = []
        resolved_threads: list[str] = []
        extracted_ids: list[str] = []
        for event in case.events:
            if event.scene != plan.index:
                continue
            if event.text.casefold() in text:
                changes.append(
                    StateChange(
                        path=event.state_path,
                        value=event.state_value,
                        event_id=event.id,
                    )
                )
                extracted_ids.append(event.id)
                if event.kind == "resolve" and event.thread_id:
                    resolved_threads.append(event.thread_id)
        delta = StoryStateDelta(
            scene_id=plan.scene_id,
            changes=tuple(changes),
            resolved_threads=tuple(resolved_threads),
            proposed_by="state_extractor",
        )
        usage = estimate_usage(document.full_text, str(delta.changes))
        return delta, usage

    def validate_candidate(
        self,
        case: EvalCase,
        plan: ScenePlan,
        document: SceneDocument,
        delta: StoryStateDelta,
    ) -> ValidationResult:
        errors: list[str] = []
        text = document.full_text.casefold()
        for fact in plan.required_facts:
            if fact.casefold() not in text:
                errors.append(f"required fact missing in {plan.scene_id}: {fact}")
        for reveal in plan.forbidden_reveals:
            if reveal.casefold() in text:
                errors.append(f"forbidden reveal appeared before boundary: {reveal}")
        if delta.proposed_by != "state_extractor":
            errors.append("only state_extractor may propose StoryStateDelta")
        for canon in case.canon_facts:
            if canon.locked and any(phrase.casefold() in text for phrase in canon.negative_phrases):
                errors.append(f"locked canon contradiction: {canon.id}")
        return ValidationResult(passed=not errors, errors=tuple(errors))

    def critic(self, document: SceneDocument, plan: ScenePlan) -> CriticResult:
        paragraphs = [block.text for block in document.blocks]
        issues: list[str] = []
        # The fixture padder cycles a small set of neutral paragraphs to reach
        # long targets. Flag only adjacent duplication, which is the deterministic
        # proxy for a broken generation rather than harmless distant recurrence.
        if any(left == right for left, right in zip(paragraphs, paragraphs[1:])):
            issues.append("duplicate paragraph")
        if document.word_count < max(1, int(plan.target_words * 0.9)):
            issues.append("scene is below the fixture word-count floor")
        return CriticResult(passed=not issues, issues=tuple(issues))

    def commit_delta(
        self,
        state: StoryState,
        delta: StoryStateDelta,
        *,
        expected_version: int,
        scene_index: int,
        canon_facts: tuple[CanonFact, ...],
    ) -> StoryState:
        """Simulate the authoritative domain-side atomic commit."""

        if state.version != expected_version:
            raise DomainConflictError(
                f"stale state version: expected {expected_version}, actual {state.version}"
            )
        if delta.proposed_by != "state_extractor":
            raise DomainConflictError("non-extractor delta rejected")
        next_state = state.clone()
        for change in delta.changes:
            for canon in canon_facts:
                # A fixture state path may be used to represent the same locked
                # fact. Contradictions are rejected before mutation.
                if canon.locked and change.value == canon.value and any(
                    phrase.casefold() in change.value.casefold()
                    for phrase in canon.negative_phrases
                ):
                    raise DomainConflictError(f"locked canon conflict: {canon.id}")
            _set_path(next_state, change.path, change.value)
        for thread_id in delta.resolved_threads:
            if thread_id not in next_state.resolved_threads:
                next_state.resolved_threads.append(thread_id)
            if thread_id in next_state.open_threads:
                next_state.open_threads.remove(thread_id)
        next_state.version += 1
        next_state.scene_index = scene_index
        return next_state

    def generate(self, case: EvalCase, variant: SystemVariant) -> StoryRun:
        if variant not in {SystemVariant.STRUCTURED_C, SystemVariant.STRUCTURED_QA_D}:
            raise ValueError(f"structured engine cannot run {variant.value}")
        premise = self.interpret_intent(case)
        blueprint = self.architect(case, premise)
        plans = self.plan_scenes(case, blueprint)
        state = StoryState(open_threads=list(case.critical_threads))
        documents: list[SceneDocument] = []
        extracted_event_ids: list[str] = []
        committed_scene_ids: list[str] = []
        validation_errors: list[str] = []
        usage = Usage()

        for plan in plans:
            writer = self.write_scene(case, plan, state)
            delta, extractor_usage = self.extract_state_delta(case, plan, writer.document, state)
            validation = self.validate_candidate(case, plan, writer.document, delta)
            usage = usage.add(writer.usage).add(extractor_usage)
            if variant is SystemVariant.STRUCTURED_QA_D:
                critic = self.critic(writer.document, plan)
                if not critic.passed:
                    validation_errors.extend(critic.issues)
            if not validation.passed:
                validation_errors.extend(validation.errors)
                # A real implementation would perform a bounded repair or
                # reject the candidate. The fixture writer is deterministic, so
                # stop rather than silently committing an invalid candidate.
                break
            try:
                state = self.commit_delta(
                    state,
                    delta,
                    expected_version=state.version,
                    scene_index=plan.index,
                    canon_facts=case.canon_facts,
                )
            except DomainConflictError as error:
                validation_errors.append(str(error))
                break
            documents.append(writer.document)
            committed_scene_ids.append(plan.scene_id)
            extracted_event_ids.extend(
                event.id
                for event in case.events
                if event.scene == plan.index and event.text.casefold() in writer.document.full_text.casefold()
            )

        return StoryRun(
            variant=variant,
            documents=documents,
            final_state=state,
            extracted_event_ids=extracted_event_ids,
            committed_scene_ids=committed_scene_ids,
            schema_valid=not validation_errors,
            validation_errors=validation_errors,
            usage=usage,
            notes=[
                "hierarchical fixture pipeline",
                "writer returns document only",
                "extractor is sole delta producer",
            ],
        )


def run_structured(case: EvalCase, variant: SystemVariant) -> StoryRun:
    return StructuredStoryEngine().generate(case, variant)
