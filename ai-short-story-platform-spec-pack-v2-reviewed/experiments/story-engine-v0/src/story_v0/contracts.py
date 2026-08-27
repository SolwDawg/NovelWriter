"""Small, explicit contracts shared by the V0 engine and its eval runner.

The production plan eventually moves these contracts into the cross-runtime
packages. V0 keeps them local and dependency-free so the proof harness is
reproducible on a clean Python installation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import copy
import json
import re
from typing import Any, Mapping


class ContractValidationError(ValueError):
    """Raised when a fixture or generated structured contract is invalid."""


class SystemVariant(str, Enum):
    BASELINE_A = "baseline_a"
    BASELINE_B = "baseline_b"
    STRUCTURED_C = "structured_c"
    STRUCTURED_QA_D = "structured_qa_d"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class CanonFact:
    id: str
    subject: str
    predicate: str
    value: str
    locked: bool = True
    positive_phrases: tuple[str, ...] = ()
    negative_phrases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("id", "subject", "predicate", "value"):
            _require_text(getattr(self, name), name)
        object.__setattr__(self, "positive_phrases", tuple(self.positive_phrases))
        object.__setattr__(self, "negative_phrases", tuple(self.negative_phrases))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CanonFact":
        return cls(
            id=str(data["id"]),
            subject=str(data["subject"]),
            predicate=str(data["predicate"]),
            value=str(data["value"]),
            locked=bool(data.get("locked", True)),
            positive_phrases=tuple(data.get("positive_phrases", ())),
            negative_phrases=tuple(data.get("negative_phrases", ())),
        )


@dataclass(frozen=True)
class SceneEvent:
    scene: int
    id: str
    text: str
    state_path: str
    state_value: str
    kind: str = "set"
    thread_id: str | None = None

    def __post_init__(self) -> None:
        if self.scene < 1:
            raise ContractValidationError("event scene must be >= 1")
        for name in ("id", "text", "state_path", "state_value"):
            _require_text(getattr(self, name), name)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SceneEvent":
        return cls(
            scene=int(data["scene"]),
            id=str(data["id"]),
            text=str(data["text"]),
            state_path=str(data["state_path"]),
            state_value=str(data["state_value"]),
            kind=str(data.get("kind", "set")),
            thread_id=str(data["thread_id"]) if data.get("thread_id") else None,
        )


@dataclass(frozen=True)
class RequiredOutcome:
    scene: int
    text: str

    def __post_init__(self) -> None:
        if self.scene < 1:
            raise ContractValidationError("required outcome scene must be >= 1")
        _require_text(self.text, "required outcome text")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RequiredOutcome":
        return cls(scene=int(data["scene"]), text=str(data["text"]))


@dataclass(frozen=True)
class ForbiddenReveal:
    before_scene: int
    text: str

    def __post_init__(self) -> None:
        if self.before_scene < 1:
            raise ContractValidationError("forbidden reveal boundary must be >= 1")
        _require_text(self.text, "forbidden reveal text")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ForbiddenReveal":
        return cls(before_scene=int(data["before_scene"]), text=str(data["text"]))


@dataclass(frozen=True)
class EvalCase:
    id: str
    premise: str
    target_words: int
    genre: str
    hard_constraints: tuple[str, ...]
    language: str = "vi-VN"
    continuity_traps: tuple[str, ...] = ()
    canon_facts: tuple[CanonFact, ...] = ()
    events: tuple[SceneEvent, ...] = ()
    required_outcomes: tuple[RequiredOutcome, ...] = ()
    forbidden_reveals: tuple[ForbiddenReveal, ...] = ()
    critical_threads: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.id, "id")
        _require_text(self.premise, "premise")
        if not 3000 <= self.target_words <= 15000:
            raise ContractValidationError("target_words must be between 3000 and 15000")
        if self.genre not in {"Mystery", "Thriller", "Horror"}:
            raise ContractValidationError(
                "V0 fixture genre must be Mystery, Thriller, or Horror"
            )
        if not self.hard_constraints:
            raise ContractValidationError("at least one hard constraint is required")
        for field_name in (
            "hard_constraints",
            "continuity_traps",
            "canon_facts",
            "events",
            "required_outcomes",
            "forbidden_reveals",
            "critical_threads",
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))
        event_ids = [event.id for event in self.events]
        if len(event_ids) != len(set(event_ids)):
            raise ContractValidationError("event IDs must be unique within a case")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvalCase":
        return cls(
            id=str(data["id"]),
            premise=str(data["premise"]),
            target_words=int(data["target_words"]),
            genre=str(data["genre"]),
            hard_constraints=tuple(data["hard_constraints"]),
            language=str(data.get("language", "vi-VN")),
            continuity_traps=tuple(data.get("continuity_traps", ())),
            canon_facts=tuple(
                CanonFact.from_dict(item) for item in data.get("canon_facts", ())
            ),
            events=tuple(SceneEvent.from_dict(item) for item in data.get("events", ())),
            required_outcomes=tuple(
                RequiredOutcome.from_dict(item)
                for item in data.get("required_outcomes", ())
            ),
            forbidden_reveals=tuple(
                ForbiddenReveal.from_dict(item)
                for item in data.get("forbidden_reveals", ())
            ),
            critical_threads=tuple(data.get("critical_threads", ())),
        )

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True)
class Premise:
    raw_idea: str
    normalized_idea: str
    language: str
    genre: str
    target_words: int


@dataclass(frozen=True)
class Blueprint:
    title: str
    logline: str
    protagonist: str
    central_conflict: str
    reversals: tuple[str, ...]
    climax: str
    resolution: str
    scene_count: int


@dataclass(frozen=True)
class ScenePlan:
    scene_id: str
    index: int
    purpose: str
    required_outcome: str
    required_facts: tuple[str, ...]
    forbidden_reveals: tuple[str, ...]
    active_threads: tuple[str, ...]
    target_tension: int
    target_words: int
    pov: str | None = None
    location: str | None = None
    participants: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.index < 1 or self.target_words < 1:
            raise ContractValidationError("scene index/target_words must be positive")
        if not 1 <= self.target_tension <= 10:
            raise ContractValidationError("target_tension must be between 1 and 10")
        for field_name in (
            "required_facts",
            "forbidden_reveals",
            "active_threads",
            "participants",
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))


@dataclass(frozen=True)
class SceneBlock:
    id: str
    type: str
    text: str
    speaker_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.id, "block id")
        _require_text(self.type, "block type")
        if not isinstance(self.text, str):
            raise ContractValidationError("block text must be a string")


@dataclass(frozen=True)
class SceneDocument:
    scene_id: str
    revision: int
    blocks: tuple[SceneBlock, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        _require_text(self.scene_id, "scene_id")
        if self.revision < 1 or self.schema_version < 1:
            raise ContractValidationError("document revision/schema_version must be positive")
        object.__setattr__(self, "blocks", tuple(self.blocks))
        block_ids = [block.id for block in self.blocks]
        if not block_ids or len(block_ids) != len(set(block_ids)):
            raise ContractValidationError("scene document requires unique stable block IDs")

    @property
    def full_text(self) -> str:
        return "\n".join(block.text for block in self.blocks if block.text)

    @property
    def word_count(self) -> int:
        return len(re.findall(r"\b[\w'-]+\b", self.full_text, flags=re.UNICODE))

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, other: "Usage") -> "Usage":
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            estimated_cost_usd=self.estimated_cost_usd + other.estimated_cost_usd,
        )


@dataclass(frozen=True)
class SceneWriterResult:
    document: SceneDocument
    usage: Usage
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class StateChange:
    path: str
    value: Any
    event_id: str
    operation: str = "set"


@dataclass(frozen=True)
class StoryStateDelta:
    scene_id: str
    changes: tuple[StateChange, ...]
    opened_threads: tuple[str, ...] = ()
    resolved_threads: tuple[str, ...] = ()
    proposed_by: str = "state_extractor"
    schema_version: int = 1

    def __post_init__(self) -> None:
        _require_text(self.scene_id, "delta scene_id")
        object.__setattr__(self, "changes", tuple(self.changes))
        object.__setattr__(self, "opened_threads", tuple(self.opened_threads))
        object.__setattr__(self, "resolved_threads", tuple(self.resolved_threads))
        if self.schema_version < 1:
            raise ContractValidationError("delta schema_version must be positive")


@dataclass
class StoryState:
    schema_version: int = 1
    version: int = 0
    scene_index: int = 0
    characters: dict[str, dict[str, Any]] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)
    inventory: dict[str, str] = field(default_factory=dict)
    locations: dict[str, str] = field(default_factory=dict)
    timeline: list[str] = field(default_factory=list)
    open_threads: list[str] = field(default_factory=list)
    resolved_threads: list[str] = field(default_factory=list)

    def clone(self) -> "StoryState":
        return copy.deepcopy(self)

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass
class StoryRun:
    variant: SystemVariant
    documents: list[SceneDocument]
    final_state: StoryState
    extracted_event_ids: list[str]
    committed_scene_ids: list[str]
    schema_valid: bool
    validation_errors: list[str] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    latency_ms: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n\n".join(document.full_text for document in self.documents)

    @property
    def word_count(self) -> int:
        return len(re.findall(r"\b[\w'-]+\b", self.full_text, flags=re.UNICODE))


@dataclass(frozen=True)
class EvalRunResult:
    case_id: str
    variant: SystemVariant
    metrics: Mapping[str, Any]
    story_path: str | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(
            {
                "case_id": self.case_id,
                "variant": self.variant.value,
                "metrics": dict(self.metrics),
                "story_path": self.story_path,
                "notes": list(self.notes),
            }
        )


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return _jsonable(asdict(value))
    return value


def dumps_contract(value: Any) -> str:
    """Serialize a contract deterministically for artifact/eval snapshots."""

    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True)

