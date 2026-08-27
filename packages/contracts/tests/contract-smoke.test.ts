import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import Ajv from "ajv";
import {
  CONTRACT_NAMES,
  CONTRACT_SCHEMA_VERSION,
} from "../generated/index.js";

const here = dirname(fileURLToPath(import.meta.url));
const schemaDir = join(here, "..", "schemas");
const fixture = JSON.parse(
  readFileSync(join(here, "..", "fixtures", "story-contracts.json"), "utf8"),
) as Record<string, unknown>;

const schemaFiles: Record<string, string> = {
  StoryIntent: "story-intent.schema.json",
  StoryBlueprint: "story-blueprint.schema.json",
  ScenePlan: "scene-plan.schema.json",
  SceneDocumentArtifact: "scene-document-artifact.schema.json",
  StoryState: "story-state.schema.json",
  StoryStateDelta: "story-state-delta.schema.json",
  AIArtifactRef: "ai-artifact-ref.schema.json",
  AIUsage: "ai-usage.schema.json",
};

const fixtureKeys: Record<string, string> = {
  StoryIntent: "story_intent",
  StoryBlueprint: "story_blueprint",
  ScenePlan: "scene_plan",
  SceneDocumentArtifact: "scene_document_artifact",
  StoryState: "story_state",
  StoryStateDelta: "story_state_delta",
  AIArtifactRef: "ai_artifact_ref",
  AIUsage: "ai_usage",
};

test("canonical schemas validate the shared fixture", () => {
  const ajv = new Ajv({ allErrors: true, strict: false });
  for (const name of CONTRACT_NAMES) {
    const schema = JSON.parse(
      readFileSync(join(schemaDir, schemaFiles[name]), "utf8"),
    ) as object;
    const validate = ajv.compile(schema);
    const valid = validate(fixture[fixtureKeys[name]]);
    assert.equal(valid, true, `${name}: ${JSON.stringify(validate.errors)}`);
  }
});

test("generated TypeScript equivalent stays aligned with the contract index", () => {
  assert.equal(CONTRACT_SCHEMA_VERSION, 1);
  assert.deepEqual([...CONTRACT_NAMES], [
    "StoryIntent",
    "StoryBlueprint",
    "ScenePlan",
    "SceneDocumentArtifact",
    "StoryState",
    "StoryStateDelta",
    "AIArtifactRef",
    "AIUsage",
  ]);
});
