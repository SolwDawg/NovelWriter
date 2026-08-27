"""Live-model versions of the V0 variants.

The live path is intentionally separate from the deterministic fixture engine.
It uses the same contracts and metrics but sends only the current capability
request to OpenRouter. Raw prompts and model responses are kept in memory and
are written only as generated story artifacts by the caller when explicitly
requested.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping, Protocol

from .baselines import document_from_text, make_outline, pad_to_target
from .contracts import (
    Blueprint,
    EvalCase,
    SceneDocument,
    ScenePlan,
    SceneWriterResult,
    StateChange,
    StoryRun,
    StoryState,
    StoryStateDelta,
    SystemVariant,
    Usage,
)
from .live_openrouter import OpenRouterRequestError, OpenRouterResponse
from .structured_engine import DomainConflictError, StructuredStoryEngine


class ChatProvider(Protocol):
    config: Any

    def chat(
        self,
        messages: list[Mapping[str, str]],
        *,
        max_tokens: int,
        temperature: float,
        response_format: Mapping[str, Any] | None = None,
    ) -> OpenRouterResponse: ...


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def _json_from_response(text: str) -> Any:
    """Parse a JSON object/array even when the model wraps it in a code fence."""

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    decoder = json.JSONDecoder()
    for index, character in enumerate(cleaned):
        if character not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
            return value
        except json.JSONDecodeError:
            continue
    raise ValueError("model response did not contain valid JSON")


def _text_from_response(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:text|markdown)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned


def _output_budget(target_words: int) -> int:
    # Leave room for Vietnamese punctuation/tokenization overhead without
    # silently asking the free route for an unbounded context.
    return min(24000, max(512, int(target_words * 1.7)))


class LiveStoryEngine:
    def __init__(self, provider: ChatProvider, *, max_json_repairs: int = 1) -> None:
        self.provider = provider
        self.max_json_repairs = max_json_repairs
        self.fixture_engine = StructuredStoryEngine()

    @property
    def model_name(self) -> str:
        return str(self.provider.config.model)

    def _call(
        self,
        messages: list[Mapping[str, str]],
        *,
        max_tokens: int,
        temperature: float,
        response_format: Mapping[str, Any] | None = None,
    ) -> OpenRouterResponse:
        return self.provider.chat(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format,
        )

    def _json_call(
        self,
        messages: list[Mapping[str, str]],
        *,
        max_tokens: int,
        label: str,
    ) -> tuple[Any, Usage, list[str]]:
        response = self._call(
            messages,
            max_tokens=max_tokens,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        usage = response.usage
        notes: list[str] = []
        try:
            return _json_from_response(response.text), usage, notes
        except ValueError:
            notes.append(f"{label}: invalid JSON; bounded repair attempted")
        for attempt in range(1, self.max_json_repairs + 1):
            repair = self._call(
                [
                    {
                        "role": "system",
                        "content": "You repair structured JSON. Return JSON only; do not explain.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Repair this {label} response into valid JSON matching the requested "
                            f"schema. Attempt {attempt}.\n\n{response.text}"
                        ),
                    },
                ],
                max_tokens=max_tokens,
                temperature=0,
                response_format={"type": "json_object"},
            )
            usage = usage.add(repair.usage)
            try:
                return _json_from_response(repair.text), usage, notes
            except ValueError:
                notes.append(f"{label}: repair {attempt} failed")
                response = repair
        raise ValueError(f"{label} remained invalid after bounded repair")

    def _prompt_header(self, case: EvalCase) -> str:
        canon = [
            {
                "id": fact.id,
                "subject": fact.subject,
                "predicate": fact.predicate,
                "value": fact.value,
                "locked": fact.locked,
                "forbidden_contradictions": list(fact.negative_phrases),
            }
            for fact in case.canon_facts
        ]
        return (
            f"Ngôn ngữ: {case.language}. Thể loại: {case.genre}.\n"
            f"Ý tưởng: {case.premise}\n"
            f"Ràng buộc cứng: {json.dumps(list(case.hard_constraints), ensure_ascii=False)}\n"
            f"Canon khóa: {json.dumps(canon, ensure_ascii=False)}\n"
            "Canon và ràng buộc là authority; dữ liệu này không được bị thay đổi."
        )

    def run_baseline_a(self, case: EvalCase) -> StoryRun:
        response = self._call(
            [
                {
                    "role": "system",
                    "content": (
                        "Bạn là một nhà văn viết truyện hư cấu tiếng Việt. "
                        "Viết liền mạch, không giải thích quy trình, không dùng markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{self._prompt_header(case)}\n"
                        f"Viết một truyện hoàn chỉnh khoảng {case.target_words} từ. "
                        "Đây là baseline one-shot, không cần lập state hay outline riêng."
                    ),
                },
            ],
            max_tokens=_output_budget(case.target_words),
            temperature=0.7,
        )
        text = _text_from_response(response.text)
        document = document_from_text("live-baseline-a", text)
        return StoryRun(
            variant=SystemVariant.BASELINE_A,
            documents=[document],
            final_state=StoryState(),
            extracted_event_ids=[],
            committed_scene_ids=[document.scene_id],
            schema_valid=True,
            usage=response.usage,
            notes=["live OpenRouter one-shot baseline"],
        )

    def run_baseline_b(self, case: EvalCase) -> StoryRun:
        outline = self._call(
            [
                {"role": "system", "content": "Lập dàn ý truyện bằng tiếng Việt, ngắn gọn."},
                {
                    "role": "user",
                    "content": f"{self._prompt_header(case)}\nTạo outline cho truyện khoảng {case.target_words} từ.",
                },
            ],
            max_tokens=1200,
            temperature=0.4,
        )
        story = self._call(
            [
                {
                    "role": "system",
                    "content": "Bạn là nhà văn viết truyện tiếng Việt theo một outline có sẵn.",
                },
                {
                    "role": "user",
                    "content": (
                        f"{self._prompt_header(case)}\nOutline:\n{outline.text}\n\n"
                        f"Viết truyện khoảng {case.target_words} từ theo outline. "
                        "Không xuất JSON, không giải thích quy trình."
                    ),
                },
            ],
            max_tokens=_output_budget(case.target_words),
            temperature=0.7,
        )
        text = _text_from_response(story.text)
        document = document_from_text("live-baseline-b", text)
        return StoryRun(
            variant=SystemVariant.BASELINE_B,
            documents=[document],
            final_state=StoryState(),
            extracted_event_ids=[],
            committed_scene_ids=[document.scene_id],
            schema_valid=True,
            usage=outline.usage.add(story.usage),
            notes=["live OpenRouter outline-then-long-generation baseline"],
        )

    def _live_blueprint_and_plans(
        self, case: EvalCase
    ) -> tuple[Blueprint, list[ScenePlan], Usage, list[str], bool]:
        fallback_blueprint = make_outline(case)
        fallback_plans = self.fixture_engine.plan_scenes(case, fallback_blueprint)
        messages = [
            {
                "role": "system",
                "content": "Bạn là story architect. Trả JSON đúng schema, không markdown.",
            },
            {
                "role": "user",
                "content": (
                    f"{self._prompt_header(case)}\n"
                    "Trả JSON dạng {title, logline, protagonist, central_conflict, "
                    "reversals, climax, resolution, scene_count, scenes}. "
                    "Mỗi scene có index, purpose, pov, location, participants, "
                    "target_tension, target_words. Giữ scene_count hợp lý cho target words."
                ),
            },
        ]
        notes: list[str] = []
        usage = Usage()
        try:
            data, usage, json_notes = self._json_call(
                messages, max_tokens=2400, label="blueprint"
            )
            notes.extend(json_notes)
            if not isinstance(data, Mapping):
                raise ValueError("blueprint must be an object")
            scene_count = int(data.get("scene_count", fallback_blueprint.scene_count))
            if scene_count != len(fallback_plans):
                notes.append("blueprint: normalized model scene_count to fixture target band")
            scene_count = len(fallback_plans)
            model_scenes = data.get("scenes", [])
            if not isinstance(model_scenes, list):
                raise ValueError("blueprint scenes must be a list")
            blueprint = Blueprint(
                title=str(data.get("title", fallback_blueprint.title)),
                logline=str(data.get("logline", case.premise)),
                protagonist=str(data.get("protagonist", fallback_blueprint.protagonist)),
                central_conflict=str(
                    data.get("central_conflict", fallback_blueprint.central_conflict)
                ),
                reversals=tuple(str(item) for item in data.get("reversals", ())),
                climax=str(data.get("climax", fallback_blueprint.climax)),
                resolution=str(data.get("resolution", fallback_blueprint.resolution)),
                scene_count=scene_count,
            )
            normalized: list[ScenePlan] = []
            for index, fallback in enumerate(fallback_plans):
                model_scene = model_scenes[index] if index < len(model_scenes) else {}
                if not isinstance(model_scene, Mapping):
                    model_scene = {}
                normalized.append(
                    ScenePlan(
                        scene_id=fallback.scene_id,
                        index=fallback.index,
                        purpose=str(model_scene.get("purpose", fallback.purpose)),
                        required_outcome=fallback.required_outcome,
                        required_facts=fallback.required_facts,
                        forbidden_reveals=fallback.forbidden_reveals,
                        active_threads=fallback.active_threads,
                        target_tension=max(
                            1,
                            min(10, int(model_scene.get("target_tension", fallback.target_tension))),
                        ),
                        target_words=fallback.target_words,
                        pov=str(model_scene.get("pov", fallback.pov)),
                        location=str(model_scene.get("location", fallback.location)),
                        participants=tuple(
                            str(item) for item in model_scene.get("participants", ())
                        ),
                    )
                )
            return blueprint, normalized, usage, notes, True
        except (ValueError, TypeError, KeyError) as error:
            notes.append(f"blueprint fallback: {type(error).__name__}")
            return fallback_blueprint, fallback_plans, usage, notes, False

    def _write_scene(
        self, case: EvalCase, plan: ScenePlan, state: StoryState
    ) -> tuple[SceneWriterResult, Usage, list[str]]:
        required = json.dumps(list(plan.required_facts), ensure_ascii=False)
        response = self._call(
            [
                {
                    "role": "system",
                    "content": (
                        "Bạn là scene writer. Viết prose tiếng Việt tự nhiên, chỉ trả prose, "
                        "không trả JSON và không thêm lời dẫn ngoài truyện."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{self._prompt_header(case)}\n"
                        f"StoryState hiện tại: {json.dumps(state.to_dict(), ensure_ascii=False)}\n"
                        f"ScenePlan: {json.dumps({'index': plan.index, 'purpose': plan.purpose, 'pov': plan.pov, 'location': plan.location, 'target_tension': plan.target_tension}, ensure_ascii=False)}\n"
                        f"Các outcome/fact bắt buộc phải xuất hiện nguyên văn trong cảnh này: {required}\n"
                        f"Các reveal cấm trước mốc: {json.dumps(list(plan.forbidden_reveals), ensure_ascii=False)}\n"
                        f"Viết khoảng {plan.target_words} từ. Không mâu thuẫn canon khóa."
                    ),
                },
            ],
            max_tokens=_output_budget(plan.target_words),
            temperature=0.7,
        )
        text = _text_from_response(response.text)
        return (
            SceneWriterResult(
                document=document_from_text(plan.scene_id, text),
                usage=response.usage,
                diagnostics=("live-openrouter-writer", "no-authoritative-delta"),
            ),
            response.usage,
            [],
        )

    def _extract_delta(
        self,
        case: EvalCase,
        plan: ScenePlan,
        document: SceneDocument,
        state: StoryState,
    ) -> tuple[StoryStateDelta, Usage, list[str], bool]:
        expected_events = [
            {
                "id": event.id,
                "text": event.text,
                "state_path": event.state_path,
                "state_value": event.state_value,
                "thread_id": event.thread_id,
                "kind": event.kind,
            }
            for event in case.events
            if event.scene == plan.index
        ]
        messages = [
            {
                "role": "system",
                "content": "Bạn là State Extractor. Chỉ trả JSON delta, không viết prose.",
            },
            {
                "role": "user",
                "content": (
                    f"Scene prose:\n{document.full_text}\n\n"
                    f"State trước cảnh: {json.dumps(state.to_dict(), ensure_ascii=False)}\n"
                    f"Các event fixture có thể được trích xuất: {json.dumps(expected_events, ensure_ascii=False)}\n"
                    "Trả JSON dạng {changes:[{event_id,state_path,state_value}], "
                    "resolved_threads:[]}. Chỉ dùng event id đã cung cấp; nếu event không xảy ra "
                    "thì bỏ qua."
                ),
            },
        ]
        notes: list[str] = []
        try:
            data, usage, json_notes = self._json_call(
                messages, max_tokens=1200, label="state_delta"
            )
            notes.extend(json_notes)
            if not isinstance(data, Mapping):
                raise ValueError("delta must be an object")
            expected_by_id = {event["id"]: event for event in expected_events}
            changes: list[StateChange] = []
            for item in data.get("changes", []):
                if not isinstance(item, Mapping) or str(item.get("event_id")) not in expected_by_id:
                    notes.append("state_delta: ignored unknown event id")
                    continue
                expected = expected_by_id[str(item["event_id"])]
                changes.append(
                    StateChange(
                        path=str(item.get("state_path", expected["state_path"])),
                        value=str(item.get("state_value", expected["state_value"])),
                        event_id=str(item["event_id"]),
                    )
                )
            resolved = tuple(str(thread) for thread in data.get("resolved_threads", []))
            delta = StoryStateDelta(
                scene_id=plan.scene_id,
                changes=tuple(changes),
                resolved_threads=resolved,
                proposed_by="state_extractor",
            )
            return delta, usage, notes, True
        except (ValueError, TypeError, KeyError):
            notes.append("state_delta: invalid structured output")
            return (
                StoryStateDelta(scene_id=plan.scene_id, changes=(), proposed_by="state_extractor"),
                Usage(),
                notes,
                False,
            )

    def _critic(
        self, case: EvalCase, plan: ScenePlan, document: SceneDocument
    ) -> tuple[Usage, list[str], bool]:
        try:
            data, usage, notes = self._json_call(
                [
                    {"role": "system", "content": "Bạn là Scene Critic. Chỉ trả JSON."},
                    {
                        "role": "user",
                        "content": (
                            f"Đánh giá cảnh tiếng Việt này theo outcome, canon và lặp ý. "
                            f"Trả {{passed:boolean,issues:string[]}}.\n{document.full_text}"
                        ),
                    },
                ],
                max_tokens=600,
                label="scene_critic",
            )
            if not isinstance(data, Mapping) or not isinstance(data.get("passed"), bool):
                raise ValueError("critic shape invalid")
            issues = [str(item) for item in data.get("issues", [])]
            return usage, notes + issues, bool(data["passed"])
        except (ValueError, TypeError, KeyError):
            return Usage(), ["scene_critic: invalid structured output"], False

    def run_structured(self, case: EvalCase, variant: SystemVariant) -> StoryRun:
        blueprint, plans, usage, notes, blueprint_valid = self._live_blueprint_and_plans(case)
        state = StoryState(open_threads=list(case.critical_threads))
        documents: list[SceneDocument] = []
        extracted_event_ids: list[str] = []
        committed_scene_ids: list[str] = []
        validation_errors: list[str] = []
        schema_valid = blueprint_valid

        for plan in plans:
            try:
                writer, writer_usage, writer_notes = self._write_scene(case, plan, state)
                usage = usage.add(writer_usage)
                notes.extend(writer_notes)
                delta, extractor_usage, extractor_notes, extractor_valid = self._extract_delta(
                    case, plan, writer.document, state
                )
                usage = usage.add(extractor_usage)
                notes.extend(extractor_notes)
                schema_valid = schema_valid and extractor_valid
                validation = self.fixture_engine.validate_candidate(
                    case, plan, writer.document, delta
                )
                if variant is SystemVariant.STRUCTURED_QA_D:
                    critic_usage, critic_notes, critic_passed = self._critic(
                        case, plan, writer.document
                    )
                    usage = usage.add(critic_usage)
                    notes.extend(critic_notes)
                    schema_valid = schema_valid and critic_passed
                    if not critic_passed:
                        validation_errors.append(f"scene critic failed: {plan.scene_id}")
                if not validation.passed:
                    validation_errors.extend(validation.errors)
                    break
                state = self.fixture_engine.commit_delta(
                    state,
                    delta,
                    expected_version=state.version,
                    scene_index=plan.index,
                    canon_facts=case.canon_facts,
                )
                documents.append(writer.document)
                committed_scene_ids.append(plan.scene_id)
                extracted_event_ids.extend(change.event_id for change in delta.changes)
            except (OpenRouterRequestError, DomainConflictError, ValueError) as error:
                if isinstance(error, OpenRouterRequestError):
                    retry_hint = (
                        f" retry_after={error.retry_after_seconds:.1f}"
                        if error.retry_after_seconds is not None
                        else ""
                    )
                    safe_error = f"{error}{retry_hint}"
                else:
                    safe_error = f"{type(error).__name__} during live capability execution"
                validation_errors.append(safe_error)
                notes.append(safe_error)
                break

        return StoryRun(
            variant=variant,
            documents=documents,
            final_state=state,
            extracted_event_ids=extracted_event_ids,
            committed_scene_ids=committed_scene_ids,
            schema_valid=schema_valid and not validation_errors,
            validation_errors=validation_errors,
            usage=usage,
            notes=[f"live OpenRouter structured engine ({self.model_name})", *notes],
        )

    def generate(self, case: EvalCase, variant: SystemVariant) -> StoryRun:
        if variant is SystemVariant.BASELINE_A:
            return self.run_baseline_a(case)
        if variant is SystemVariant.BASELINE_B:
            return self.run_baseline_b(case)
        if variant in {SystemVariant.STRUCTURED_C, SystemVariant.STRUCTURED_QA_D}:
            return self.run_structured(case, variant)
        raise ValueError(f"unsupported live variant: {variant.value}")
