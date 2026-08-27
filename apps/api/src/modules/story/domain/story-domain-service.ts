import type {
  JsonValue,
  SceneDocumentArtifact,
  StoryState,
  StoryStateDelta,
  StateChange,
} from "@story-platform/contracts";
import {
  addCanonFact,
  addCharacterRelationship,
  type CanonFact,
  type CharacterRelationship,
  updateCanonFactValue,
} from "../../story-bible/domain/story-bible.js";
import { assertSceneDocument } from "../../document/domain/scene-document.js";
import {
  cloneStory,
  type Story,
} from "./entities.js";
import { StoryDomainError } from "./errors.js";
import type {
  ApplyValidatedSceneCommand,
  ReconciliationResult,
} from "./commands.js";

const STATE_ROOTS = new Set([
  "characters",
  "facts",
  "inventory",
  "locations",
  "timeline",
  "open_threads",
  "resolved_threads",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function setStateChange(state: StoryState, change: StateChange): void {
  const segments = change.path.split(".").filter(Boolean);
  if (segments.length < 2 || !STATE_ROOTS.has(segments[0])) {
    throw new StoryDomainError(
      "INVALID_STATE_CHANGE",
      `state change must target a mutable state projection: ${change.path}`,
    );
  }

  const root = state as unknown as Record<string, unknown>;
  let cursor: Record<string, unknown> = root;
  for (const segment of segments.slice(0, -1)) {
    const current = cursor[segment];
    if (!isRecord(current)) {
      throw new StoryDomainError(
        "INVALID_STATE_CHANGE",
        `state path is not an object path: ${change.path}`,
      );
    }
    cursor = current;
  }

  const leaf = segments.at(-1)!;
  if (change.operation === "set") {
    cursor[leaf] = structuredClone(change.value);
    return;
  }
  if (change.operation === "unset") {
    delete cursor[leaf];
    return;
  }

  const current = cursor[leaf];
  if (!Array.isArray(current)) {
    throw new StoryDomainError(
      "INVALID_STATE_CHANGE",
      `append requires an array at ${change.path}`,
    );
  }
  current.push(structuredClone(change.value));
}

function applyDeltaToState(state: StoryState, delta: StoryStateDelta, nextSceneIndex: number): StoryState {
  const nextState = structuredClone(state);
  for (const change of delta.changes) setStateChange(nextState, change);
  nextState.version = state.version + 1;
  nextState.scene_index = nextSceneIndex;
  return nextState;
}

function setDirtyBoundary(story: Story, sceneId: string): void {
  const affectedIndex = story.committedSceneIds.indexOf(sceneId);
  if (affectedIndex < 0) return;

  const currentIndex = story.dirtyFromSceneId
    ? story.committedSceneIds.indexOf(story.dirtyFromSceneId)
    : Number.POSITIVE_INFINITY;
  if (affectedIndex < currentIndex || !story.dirtyFromSceneId) {
    story.dirtyFromSceneId = story.committedSceneIds[affectedIndex];
  }
  if (story.consistencyStatus !== "NEEDS_REVIEW") {
    story.consistencyStatus = "DIRTY";
  }
}

function findDocumentByArtifactId(story: Story, artifactId: string): SceneDocumentArtifact {
  const document = Object.values(story.documentsBySceneId).find(
    (candidate) => candidate.artifact_id === artifactId,
  );
  if (!document) {
    throw new StoryDomainError(
      "INVALID_SCENE_COMMIT",
      `unknown scene document artifact: ${artifactId}`,
    );
  }
  return document;
}

function assertDeltaAuthority(sceneId: string, delta: StoryStateDelta): void {
  if (delta.schema_version !== 1 || delta.scene_id !== sceneId) {
    throw new StoryDomainError(
      "INVALID_SCENE_COMMIT",
      "delta schema or scene ID does not match the commit",
    );
  }
  if (delta.proposed_by !== "state_extractor") {
    throw new StoryDomainError(
      "DELTA_AUTHORITY_VIOLATION",
      "only state_extractor may propose StoryStateDelta",
    );
  }
}

export function registerSceneDocument(
  story: Story,
  document: SceneDocumentArtifact,
): Story {
  assertSceneDocument(document);
  const next = cloneStory(story);
  next.documentsBySceneId[document.scene_id] = structuredClone(document);
  next.version += 1;
  return next;
}

export function applyValidatedScene(
  story: Story,
  command: ApplyValidatedSceneCommand,
): Story {
  if (command.storyId !== story.id) {
    throw new StoryDomainError("INVALID_SCENE_COMMIT", "command story ID does not match aggregate");
  }

  const previousIdempotentScene = story.appliedIdempotencyKeys[command.idempotencyKey];
  if (previousIdempotentScene) {
    if (previousIdempotentScene !== command.sceneId) {
      throw new StoryDomainError(
        "IDEMPOTENCY_CONFLICT",
        `idempotency key was already used for ${previousIdempotentScene}`,
      );
    }
    return cloneStory(story);
  }

  if (story.consistencyStatus !== "CLEAN") {
    throw new StoryDomainError(
      "STORY_NOT_CLEAN",
      "downstream generation is blocked until story reconciliation completes",
    );
  }
  if (command.expectedStateVersion !== story.state.version) {
    throw new StoryDomainError(
      "STALE_STATE_VERSION",
      `expected state ${command.expectedStateVersion}, current state is ${story.state.version}`,
    );
  }
  if (command.expectedCanonVersion !== story.canonVersion) {
    throw new StoryDomainError(
      "STALE_CANON_VERSION",
      `expected canon ${command.expectedCanonVersion}, current canon is ${story.canonVersion}`,
    );
  }
  if (story.committedSceneIds.includes(command.sceneId)) {
    throw new StoryDomainError("DUPLICATE_SCENE", `scene already committed: ${command.sceneId}`);
  }

  const document = findDocumentByArtifactId(story, command.documentArtifactId);
  if (document.scene_id !== command.sceneId) {
    throw new StoryDomainError(
      "INVALID_SCENE_COMMIT",
      "document artifact does not belong to the committed scene",
    );
  }
  assertDeltaAuthority(command.sceneId, command.delta);

  const next = cloneStory(story);
  next.state = applyDeltaToState(
    next.state,
    command.delta,
    next.committedSceneIds.length + 1,
  );
  next.committedSceneIds.push(command.sceneId);
  next.deltasBySceneId[command.sceneId] = structuredClone(command.delta);
  next.appliedIdempotencyKeys[command.idempotencyKey] = command.sceneId;
  next.version += 1;
  return next;
}

export function assertGenerationAllowed(story: Story): void {
  if (story.consistencyStatus !== "CLEAN") {
    throw new StoryDomainError(
      "RECONCILIATION_REQUIRED",
      `story is ${story.consistencyStatus}; reconcile before downstream generation`,
    );
  }
}

export function markScenePotentiallyChanged(story: Story, sceneId: string): Story {
  const next = cloneStory(story);
  if (!next.committedSceneIds.includes(sceneId)) return next;
  setDirtyBoundary(next, sceneId);
  next.version += 1;
  return next;
}

export function beginReconciliation(story: Story): Story {
  if (!story.dirtyFromSceneId) {
    throw new StoryDomainError("RECONCILIATION_REQUIRED", "story has no dirty scene boundary");
  }
  const next = cloneStory(story);
  next.consistencyStatus = "RECONCILING";
  next.version += 1;
  return next;
}

export function completeReconciliation(
  story: Story,
  result: ReconciliationResult,
): Story {
  if (story.consistencyStatus !== "RECONCILING") {
    throw new StoryDomainError(
      "RECONCILIATION_REQUIRED",
      "reconciliation must be started before it can complete",
    );
  }

  const next = cloneStory(story);
  if (result.unresolvedReasons?.length) {
    next.consistencyStatus = "NEEDS_REVIEW";
    next.version += 1;
    return next;
  }

  next.state = structuredClone(result.reconciledState);
  next.consistencyStatus = "CLEAN";
  next.dirtyFromSceneId = null;
  next.version += 1;
  return next;
}

export function addStoryRelationship(
  story: Story,
  relationship: CharacterRelationship,
): Story {
  const next = cloneStory(story);
  next.bible = addCharacterRelationship(next.bible, relationship);
  next.canonVersion += 1;
  if (next.committedSceneIds.length) setDirtyBoundary(next, next.committedSceneIds[0]);
  next.version += 1;
  return next;
}

export function addStoryCanonFact(story: Story, fact: CanonFact): Story {
  const next = cloneStory(story);
  next.bible = addCanonFact(next.bible, fact);
  next.canonVersion += 1;
  if (next.committedSceneIds.length) setDirtyBoundary(next, next.committedSceneIds[0]);
  next.version += 1;
  return next;
}

export function updateStoryCanonFact(
  story: Story,
  factId: string,
  value: JsonValue,
): Story {
  const next = cloneStory(story);
  next.bible = updateCanonFactValue(next.bible, factId, value);
  if (JSON.stringify(story.bible.canonFacts[factId]?.value) === JSON.stringify(value)) {
    return next;
  }
  next.canonVersion += 1;
  if (next.committedSceneIds.length) setDirtyBoundary(next, next.committedSceneIds[0]);
  next.version += 1;
  return next;
}
