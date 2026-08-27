/**
 * Runtime-neutral TypeScript equivalents for the canonical JSON Schemas.
 * Keep schema files as the source of truth; regenerate/update this file when
 * a contract changes.
 */

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonValue[];
export interface JsonObject {
  [key: string]: JsonValue;
}

export interface StoryIntent {
  schema_version: 1;
  story_id?: string;
  project_id?: string;
  raw_idea: string;
  normalized_idea?: string;
  language: string;
  genre: "Mystery" | "Thriller" | "Horror";
  target_words: number;
  hard_constraints: string[];
  continuity_traps?: string[];
}

export interface StoryBlueprint {
  schema_version: 1;
  title: string;
  logline: string;
  protagonist: string;
  central_conflict: string;
  reversals: string[];
  climax: string;
  resolution: string;
  scene_count: number;
  language?: string;
  genre?: "Mystery" | "Thriller" | "Horror";
}

export interface ScenePlan {
  schema_version: 1;
  scene_id: string;
  index: number;
  purpose: string;
  required_outcome: string;
  required_facts: string[];
  forbidden_reveals: string[];
  active_threads: string[];
  target_tension: number;
  target_words: number;
  pov?: string;
  location?: string;
  participants?: string[];
}

export interface SceneBlock {
  id: string;
  type: string;
  text: string;
  speaker_id?: string;
}

export interface SceneDocumentArtifact {
  schema_version: 1;
  artifact_id?: string;
  scene_id: string;
  revision: number;
  blocks: SceneBlock[];
}

export interface StoryState {
  schema_version: 1;
  version: number;
  scene_index: number;
  characters: Record<string, Record<string, JsonValue>>;
  facts: Record<string, JsonValue>;
  inventory: Record<string, string>;
  locations: Record<string, string>;
  timeline: string[];
  open_threads: string[];
  resolved_threads: string[];
}

export interface StateChange {
  path: string;
  value: JsonValue;
  event_id: string;
  operation: "set" | "unset" | "append";
}

export interface StoryStateDelta {
  schema_version: 1;
  scene_id: string;
  changes: StateChange[];
  opened_threads: string[];
  resolved_threads: string[];
  proposed_by: "state_extractor";
}

export interface AIArtifactRef {
  schema_version: 1;
  artifact_id: string;
  artifact_type?: string;
  content_hash: string;
  content_type: string;
  byte_size: number;
  storage_key: string;
  expires_at?: string;
}

export interface AIUsage {
  schema_version: 1;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  request_id?: string;
  latency_ms?: number;
}

export const CONTRACT_SCHEMA_VERSION = 1 as const;
export const CONTRACT_NAMES = [
  "StoryIntent",
  "StoryBlueprint",
  "ScenePlan",
  "SceneDocumentArtifact",
  "StoryState",
  "StoryStateDelta",
  "AIArtifactRef",
  "AIUsage",
] as const;
