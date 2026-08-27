import assert from "node:assert/strict";
import test from "node:test";
import type {
  SceneDocumentArtifact,
  StoryIntent,
  StoryStateDelta,
} from "@story-platform/contracts";
import {
  addStoryCanonFact,
  addStoryRelationship,
  applyValidatedScene,
  assertGenerationAllowed,
  beginReconciliation,
  completeReconciliation,
  createStory,
  markScenePotentiallyChanged,
  registerSceneDocument,
  StoryDomainError,
  updateStoryCanonFact,
} from "../../src/modules/story/index.js";

const intent: StoryIntent = {
  schema_version: 1,
  raw_idea: "Một người trông coi kho nghe thấy tiếng gõ từ căn phòng bị niêm phong.",
  language: "vi-VN",
  genre: "Mystery",
  target_words: 3000,
  hard_constraints: ["Không tiết lộ hung thủ trước cảnh cuối"],
};

function newStory() {
  return createStory({
    id: "story-001",
    projectId: "project-001",
    title: "Tiếng Gõ Sau Bức Tường",
    intent,
  });
}

function documentFor(sceneId: string, artifactId: string): SceneDocumentArtifact {
  return {
    schema_version: 1,
    artifact_id: artifactId,
    scene_id: sceneId,
    revision: 1,
    blocks: [
      {
        id: `${sceneId}-block-001`,
        type: "paragraph",
        text: `Nội dung đã được chấp nhận của ${sceneId}.`,
      },
    ],
  };
}

function deltaFor(sceneId: string, eventId: string, factName: string): StoryStateDelta {
  return {
    schema_version: 1,
    scene_id: sceneId,
    changes: [
      {
        path: `facts.${factName}`,
        value: true,
        event_id: eventId,
        operation: "set",
      },
    ],
    opened_threads: [],
    resolved_threads: [],
    proposed_by: "state_extractor",
  };
}

function commitScene(story: ReturnType<typeof newStory>, sceneId: string, ordinal: number) {
  const artifactId = `artifact-${sceneId}`;
  const registered = registerSceneDocument(story, documentFor(sceneId, artifactId));
  return applyValidatedScene(registered, {
    storyId: registered.id,
    sceneId,
    expectedStateVersion: registered.state.version,
    expectedCanonVersion: registered.canonVersion,
    documentArtifactId: artifactId,
    delta: deltaFor(sceneId, `event-${ordinal}`, `scene_${ordinal}_accepted`),
    idempotencyKey: `commit-${sceneId}`,
  });
}

function expectDomainError(code: string) {
  return (error: unknown): boolean =>
    error instanceof StoryDomainError && error.code === code;
}

test("a first-class relationship owns its truth instead of a duplicate generic fact", () => {
  const withRelationship = addStoryRelationship(newStory(), {
    id: "rel-nam-minh",
    subjectCharacterId: "char_nam",
    relationType: "sibling_of",
    objectCharacterId: "char_minh",
    source: "author",
  });

  assert.throws(
    () =>
      addStoryCanonFact(withRelationship, {
        id: "fact-nam-minh-sibling",
        subjectRef: "char_nam",
        predicate: "sibling_of",
        value: "char_minh",
        locked: true,
        source: "state_extractor",
      }),
    expectDomainError("ONE_AUTHORITY_VIOLATION"),
  );
});

test("a generic fact cannot be created before a matching first-class relationship", () => {
  const withFact = addStoryCanonFact(newStory(), {
    id: "fact-nam-minh-sibling",
    subjectRef: "char_nam",
    predicate: "sibling_of",
    value: "char_minh",
    locked: false,
    source: "author",
  });

  assert.throws(
    () =>
      addStoryRelationship(withFact, {
        id: "rel-nam-minh",
        subjectCharacterId: "char_nam",
        relationType: "sibling_of",
        objectCharacterId: "char_minh",
        source: "author",
      }),
    expectDomainError("ONE_AUTHORITY_VIOLATION"),
  );
});

test("a generic fact cannot later be mutated into a first-class relationship duplicate", () => {
  const withFact = addStoryCanonFact(newStory(), {
    id: "fact-nam-minh-sibling",
    subjectRef: "char_nam",
    predicate: "sibling_of",
    value: "unknown",
    locked: false,
    source: "author",
  });
  const withRelationship = addStoryRelationship(withFact, {
    id: "rel-nam-minh",
    subjectCharacterId: "char_nam",
    relationType: "sibling_of",
    objectCharacterId: "char_minh",
    source: "author",
  });

  assert.throws(
    () => updateStoryCanonFact(withRelationship, "fact-nam-minh-sibling", "char_minh"),
    expectDomainError("ONE_AUTHORITY_VIOLATION"),
  );
});

test("locked canon and stale state/canon versions fail deterministically", () => {
  const withFact = addStoryCanonFact(newStory(), {
    id: "fact-sealed-room",
    subjectRef: "room-001",
    predicate: "sealed",
    value: true,
    locked: true,
    source: "author",
  });

  const registered = registerSceneDocument(
    withFact,
    documentFor("scene-001", "artifact-scene-001"),
  );
  const command = {
    storyId: registered.id,
    sceneId: "scene-001",
    expectedStateVersion: registered.state.version,
    expectedCanonVersion: registered.canonVersion,
    documentArtifactId: "artifact-scene-001",
    delta: deltaFor("scene-001", "event-001", "knocking_heard"),
    idempotencyKey: "commit-scene-001",
  } as const;

  assert.throws(
    () =>
      applyValidatedScene(registered, {
        ...command,
        expectedStateVersion: registered.state.version + 1,
      }),
    expectDomainError("STALE_STATE_VERSION"),
  );
  assert.throws(
    () =>
      applyValidatedScene(registered, {
        ...command,
        expectedCanonVersion: registered.canonVersion - 1,
      }),
    expectDomainError("STALE_CANON_VERSION"),
  );
  assert.throws(
    () =>
      applyValidatedScene(registered, {
        ...command,
        delta: { ...command.delta, proposed_by: "writer" } as unknown as StoryStateDelta,
      }),
    expectDomainError("DELTA_AUTHORITY_VIOLATION"),
  );

  assert.throws(
    () => updateStoryCanonFact(withFact, "fact-sealed-room", false),
    expectDomainError("LOCKED_CANON_MUTATION"),
  );

  const committed = applyValidatedScene(registered, command);
  assert.equal(committed.state.facts.knocking_heard, true);
  assert.equal(committed.state.version, 1);
  assert.deepEqual(committed.committedSceneIds, ["scene-001"]);
});

test("editing an upstream committed scene marks the earliest dirty boundary and blocks generation", () => {
  let story = commitScene(newStory(), "scene-001", 1);
  story = commitScene(story, "scene-002", 2);

  story = markScenePotentiallyChanged(story, "scene-002");
  assert.equal(story.consistencyStatus, "DIRTY");
  assert.equal(story.dirtyFromSceneId, "scene-002");

  story = markScenePotentiallyChanged(story, "scene-001");
  assert.equal(story.dirtyFromSceneId, "scene-001");
  assert.throws(() => assertGenerationAllowed(story), expectDomainError("RECONCILIATION_REQUIRED"));

  const reconciling = beginReconciliation(story);
  assert.equal(reconciling.consistencyStatus, "RECONCILING");
  const clean = completeReconciliation(reconciling, {
    reconciledState: {
      ...reconciling.state,
      version: reconciling.state.version + 1,
      facts: { ...reconciling.state.facts, lan_alive: false },
    },
  });
  assert.equal(clean.consistencyStatus, "CLEAN");
  assert.equal(clean.dirtyFromSceneId, null);
  assert.equal(clean.state.facts.lan_alive, false);
  assert.doesNotThrow(() => assertGenerationAllowed(clean));
});

test("a reconciliation conflict remains visible as NEEDS_REVIEW", () => {
  const dirty = markScenePotentiallyChanged(commitScene(newStory(), "scene-001", 1), "scene-001");
  const reconciling = beginReconciliation(dirty);
  const needsReview = completeReconciliation(reconciling, {
    reconciledState: reconciling.state,
    unresolvedReasons: ["downstream scene contradicts the edited event"],
  });

  assert.equal(needsReview.consistencyStatus, "NEEDS_REVIEW");
  assert.equal(needsReview.dirtyFromSceneId, "scene-001");
  assert.throws(
    () => assertGenerationAllowed(needsReview),
    expectDomainError("RECONCILIATION_REQUIRED"),
  );
});

test("the same idempotency key returns the original commit without a second state mutation", () => {
  const story = commitScene(newStory(), "scene-001", 1);
  const document = documentFor("scene-002", "artifact-scene-002");
  const registered = registerSceneDocument(story, document);
  const command = {
    storyId: registered.id,
    sceneId: "scene-002",
    expectedStateVersion: registered.state.version,
    expectedCanonVersion: registered.canonVersion,
    documentArtifactId: document.artifact_id!,
    delta: deltaFor("scene-002", "event-002", "second_scene_accepted"),
    idempotencyKey: "commit-scene-002",
  };

  const first = applyValidatedScene(registered, command);
  const retry = applyValidatedScene(first, command);
  assert.deepEqual(retry, first);
});
