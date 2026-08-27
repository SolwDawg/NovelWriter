"""Generated Python equivalents for packages/contracts/schemas/*.json."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


CONTRACT_SCHEMA_VERSION = 1
CONTRACT_NAMES = (
    "StoryIntent",
    "StoryBlueprint",
    "ScenePlan",
    "SceneDocumentArtifact",
    "StoryState",
    "StoryStateDelta",
    "AIArtifactRef",
    "AIUsage",
)


class StoryIntent(TypedDict):
    schema_version: Literal[1]
    raw_idea: str
    language: str
    genre: Literal["Mystery", "Thriller", "Horror"]
    target_words: int
    hard_constraints: list[str]
    story_id: NotRequired[str]
    project_id: NotRequired[str]
    normalized_idea: NotRequired[str]
    continuity_traps: NotRequired[list[str]]


class StoryBlueprint(TypedDict):
    schema_version: Literal[1]
    title: str
    logline: str
    protagonist: str
    central_conflict: str
    reversals: list[str]
    climax: str
    resolution: str
    scene_count: int
    language: NotRequired[str]
    genre: NotRequired[Literal["Mystery", "Thriller", "Horror"]]


class ScenePlan(TypedDict):
    schema_version: Literal[1]
    scene_id: str
    index: int
    purpose: str
    required_outcome: str
    required_facts: list[str]
    forbidden_reveals: list[str]
    active_threads: list[str]
    target_tension: int
    target_words: int
    pov: NotRequired[str]
    location: NotRequired[str]
    participants: NotRequired[list[str]]


class SceneBlock(TypedDict):
    id: str
    type: str
    text: str
    speaker_id: NotRequired[str]


class SceneDocumentArtifact(TypedDict):
    schema_version: Literal[1]
    scene_id: str
    revision: int
    blocks: list[SceneBlock]
    artifact_id: NotRequired[str]


class StoryState(TypedDict):
    schema_version: Literal[1]
    version: int
    scene_index: int
    characters: dict[str, dict[str, Any]]
    facts: dict[str, Any]
    inventory: dict[str, str]
    locations: dict[str, str]
    timeline: list[str]
    open_threads: list[str]
    resolved_threads: list[str]


class StateChange(TypedDict):
    path: str
    value: Any
    event_id: str
    operation: Literal["set", "unset", "append"]


class StoryStateDelta(TypedDict):
    schema_version: Literal[1]
    scene_id: str
    changes: list[StateChange]
    opened_threads: list[str]
    resolved_threads: list[str]
    proposed_by: Literal["state_extractor"]


class AIArtifactRef(TypedDict):
    schema_version: Literal[1]
    artifact_id: str
    content_hash: str
    content_type: str
    byte_size: int
    storage_key: str
    artifact_type: NotRequired[str]
    expires_at: NotRequired[str]


class AIUsage(TypedDict):
    schema_version: Literal[1]
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    request_id: NotRequired[str]
    latency_ms: NotRequired[float]
