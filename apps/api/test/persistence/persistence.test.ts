import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import type { SceneDocumentArtifact, StoryState } from "@story-platform/contracts";
import { InMemoryAtomicPersistence } from "../../src/infrastructure/database/in-memory-atomic-store.js";
import { InMemorySceneDocumentRepository } from "../../src/modules/document/application/scene-document-repository.js";
import { StoryDomainError } from "../../src/modules/story/domain/errors.js";

const here = dirname(fileURLToPath(import.meta.url));

function documentFor(revision: number): SceneDocumentArtifact {
  return {
    schema_version: 1,
    artifact_id: `artifact-scene-001-r${revision}`,
    scene_id: "scene-001",
    revision,
    blocks: [
      {
        id: `scene-001-block-${revision}`,
        type: "paragraph",
        text: `Revision ${revision}`,
      },
    ],
  };
}

function stateFor(version: number): StoryState {
  return {
    schema_version: 1,
    version,
    scene_index: version,
    characters: {},
    facts: {},
    inventory: {},
    locations: {},
    timeline: [],
    open_threads: [],
    resolved_threads: [],
  };
}

function expectCode(code: string) {
  return (error: unknown): boolean =>
    error instanceof StoryDomainError && error.code === code;
}

test("a transaction rolls back document/state/outbox together on mid-commit failure", async () => {
  const persistence = new InMemoryAtomicPersistence();

  await assert.rejects(
    persistence.transaction(async (tx) => {
      tx.putDocument("scene-001", documentFor(1));
      throw new Error("simulated failure before state update");
    }),
    /simulated failure/,
  );
  assert.deepEqual(persistence.snapshot(), {
    documents: {},
    states: {},
    outbox: {},
  });

  await persistence.transaction(async (tx) => {
    tx.putDocument("scene-001", documentFor(1));
    tx.putState("story-001:state:1", stateFor(1));
    tx.putOutbox("event-001", { type: "SceneCommitted" });
  });
  assert.equal(persistence.snapshot().documents["scene-001"].revision, 1);
  assert.equal(persistence.snapshot().states["story-001:state:1"].version, 1);
  assert.equal(persistence.snapshot().outbox["event-001"].type, "SceneCommitted");
});

test("document saves require the current base revision and advance monotonically", async () => {
  const repository = new InMemorySceneDocumentRepository();
  const first = await repository.save("scene-001", documentFor(1), 0);
  assert.equal(first.revision, 1);

  await assert.rejects(
    repository.save("scene-001", documentFor(1), 0),
    expectCode("STALE_DOCUMENT_REVISION"),
  );
  await assert.rejects(
    repository.save("scene-001", documentFor(3), 1),
    expectCode("INVALID_SCENE_COMMIT"),
  );

  const second = await repository.save("scene-001", documentFor(2), 1);
  assert.equal(second.revision, 2);
  assert.equal((await repository.get("scene-001"))?.revision, 2);
});

test("the initial migration contains the product truth and atomic commit tables", () => {
  const migration = readFileSync(
    join(here, "..", "..", "src", "infrastructure", "database", "migrations", "0001_initial.sql"),
    "utf8",
  );
  for (const table of [
    "stories",
    "scenes",
    "story_states",
    "story_state_deltas",
    "scene_documents",
    "scene_versions",
    "generation_runs",
    "ai_usage",
    "scene_commit_receipts",
    "outbox_events",
  ]) {
    assert.match(migration, new RegExp(`CREATE TABLE IF NOT EXISTS ${table}`));
  }
  assert.match(migration, /CREATE EXTENSION IF NOT EXISTS vector/);
  assert.match(migration, /CREATE TABLE IF NOT EXISTS users/);
  assert.match(migration, /UNIQUE \(scene_id\)/);
  assert.match(migration, /idempotency_key text NOT NULL UNIQUE/);
});
