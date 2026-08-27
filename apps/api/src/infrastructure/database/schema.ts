import type {
  SceneDocumentArtifact,
  StoryBlueprint,
  StoryIntent,
  StoryState,
  StoryStateDelta,
} from "@story-platform/contracts";
import {
  boolean,
  integer,
  jsonb,
  numeric,
  pgTable,
  text,
  timestamp,
  uniqueIndex,
} from "drizzle-orm/pg-core";

const timestamps = {
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
};

export const users = pgTable(
  "users",
  {
    id: text("id").primaryKey(),
    email: text("email").notNull(),
    passwordHash: text("password_hash").notNull(),
    ...timestamps,
  },
  (table) => [uniqueIndex("users_email_idx").on(table.email)],
);

export const workspaces = pgTable("workspaces", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  ...timestamps,
});

export const workspaceMemberships = pgTable(
  "workspace_memberships",
  {
    id: text("id").primaryKey(),
    workspaceId: text("workspace_id").notNull(),
    userId: text("user_id").notNull(),
    role: text("role").notNull(),
    ...timestamps,
  },
  (table) => [
    uniqueIndex("workspace_memberships_workspace_user_idx").on(
      table.workspaceId,
      table.userId,
    ),
  ],
);

export const projects = pgTable("projects", {
  id: text("id").primaryKey(),
  workspaceId: text("workspace_id").notNull(),
  name: text("name").notNull(),
  ...timestamps,
});

export const stories = pgTable("stories", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull(),
  title: text("title").notNull(),
  status: text("status").notNull(),
  targetWordCount: integer("target_word_count").notNull(),
  language: text("language").notNull(),
  genre: text("genre").notNull(),
  outputMode: text("output_mode").notNull(),
  intentJson: jsonb("intent_json").$type<StoryIntent>().notNull(),
  blueprintJson: jsonb("blueprint_json").$type<StoryBlueprint | null>(),
  currentStateVersion: integer("current_state_version").notNull(),
  canonVersion: integer("canon_version").notNull(),
  consistencyStatus: text("consistency_status").notNull(),
  dirtyFromSceneId: text("dirty_from_scene_id"),
  version: integer("version").notNull(),
  ...timestamps,
});

export const chapters = pgTable("chapters", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  title: text("title").notNull(),
  ordinal: integer("ordinal").notNull(),
  ...timestamps,
});

export const scenes = pgTable("scenes", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  chapterId: text("chapter_id"),
  ordinal: integer("ordinal").notNull(),
  status: text("status").notNull(),
  currentDocumentRevision: integer("current_document_revision").notNull(),
  ...timestamps,
});

export const storyStates = pgTable(
  "story_states",
  {
    id: text("id").primaryKey(),
    storyId: text("story_id").notNull(),
    version: integer("version").notNull(),
    stateJson: jsonb("state_json").$type<StoryState>().notNull(),
    ...timestamps,
  },
  (table) => [uniqueIndex("story_states_story_version_idx").on(table.storyId, table.version)],
);

export const storyStateDeltas = pgTable(
  "story_state_deltas",
  {
    id: text("id").primaryKey(),
    storyId: text("story_id").notNull(),
    sceneId: text("scene_id").notNull(),
    stateVersion: integer("state_version").notNull(),
    deltaJson: jsonb("delta_json").$type<StoryStateDelta>().notNull(),
    ...timestamps,
  },
  (table) => [uniqueIndex("story_state_deltas_story_scene_idx").on(table.storyId, table.sceneId)],
);

export const characters = pgTable("characters", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  name: text("name").notNull(),
  profileJson: jsonb("profile_json").$type<Record<string, unknown>>().notNull(),
  ...timestamps,
});

export const characterRelationships = pgTable("character_relationships", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  subjectCharacterId: text("subject_character_id").notNull(),
  relationType: text("relation_type").notNull(),
  objectCharacterId: text("object_character_id").notNull(),
  source: text("source").notNull(),
  ...timestamps,
});

export const locations = pgTable("locations", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  name: text("name").notNull(),
  metadataJson: jsonb("metadata_json").$type<Record<string, unknown>>().notNull(),
  ...timestamps,
});

export const worldRules = pgTable("world_rules", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  ruleText: text("rule_text").notNull(),
  locked: boolean("locked").notNull(),
  ...timestamps,
});

export const storyThreads = pgTable("story_threads", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  title: text("title").notNull(),
  status: text("status").notNull(),
  metadataJson: jsonb("metadata_json").$type<Record<string, unknown>>().notNull(),
  ...timestamps,
});

export const canonFacts = pgTable("canon_facts", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  subjectRef: text("subject_ref").notNull(),
  predicate: text("predicate").notNull(),
  valueJson: jsonb("value_json").$type<unknown>().notNull(),
  locked: boolean("locked").notNull(),
  source: text("source").notNull(),
  introducedSceneId: text("introduced_scene_id"),
  ...timestamps,
});

export const sceneDocuments = pgTable(
  "scene_documents",
  {
    id: text("id").primaryKey(),
    storyId: text("story_id").notNull(),
    sceneId: text("scene_id").notNull(),
    artifactId: text("artifact_id"),
    revision: integer("revision").notNull(),
    documentJson: jsonb("document_json").$type<SceneDocumentArtifact>().notNull(),
    ...timestamps,
  },
  (table) => [uniqueIndex("scene_documents_scene_idx").on(table.sceneId)],
);

export const sceneVersions = pgTable(
  "scene_versions",
  {
    id: text("id").primaryKey(),
    storyId: text("story_id").notNull(),
    sceneId: text("scene_id").notNull(),
    revision: integer("revision").notNull(),
    source: text("source").notNull(),
    documentJson: jsonb("document_json").$type<SceneDocumentArtifact>().notNull(),
    metadataJson: jsonb("metadata_json").$type<Record<string, unknown>>().notNull(),
    ...timestamps,
  },
  (table) => [uniqueIndex("scene_versions_scene_revision_idx").on(table.sceneId, table.revision)],
);

export const generationRuns = pgTable("generation_runs", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  status: text("status").notNull(),
  idempotencyKey: text("idempotency_key"),
  metadataJson: jsonb("metadata_json").$type<Record<string, unknown>>().notNull(),
  ...timestamps,
});

export const aiUsage = pgTable("ai_usage", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  generationRunId: text("generation_run_id"),
  provider: text("provider").notNull(),
  model: text("model").notNull(),
  inputTokens: integer("input_tokens").notNull(),
  outputTokens: integer("output_tokens").notNull(),
  totalTokens: integer("total_tokens").notNull(),
  estimatedCostUsd: numeric("estimated_cost_usd", { precision: 18, scale: 8 }).notNull(),
  ...timestamps,
});

export const outboxEvents = pgTable(
  "outbox_events",
  {
    id: text("id").primaryKey(),
    aggregateType: text("aggregate_type").notNull(),
    aggregateId: text("aggregate_id").notNull(),
    eventType: text("event_type").notNull(),
    idempotencyKey: text("idempotency_key").notNull(),
    payloadJson: jsonb("payload_json").$type<Record<string, unknown>>().notNull(),
    publishedAt: timestamp("published_at", { withTimezone: true }),
    ...timestamps,
  },
  (table) => [uniqueIndex("outbox_events_idempotency_idx").on(table.idempotencyKey)],
);

export const sceneCommitReceipts = pgTable(
  "scene_commit_receipts",
  {
    id: text("id").primaryKey(),
    idempotencyKey: text("idempotency_key").notNull(),
    storyId: text("story_id").notNull(),
    sceneId: text("scene_id").notNull(),
    documentRevision: integer("document_revision").notNull(),
    resultingStateVersion: integer("resulting_state_version").notNull(),
    resultingStoryVersion: integer("resulting_story_version").notNull(),
    ...timestamps,
  },
  (table) => [uniqueIndex("scene_commit_receipts_idempotency_idx").on(table.idempotencyKey)],
);

export const databaseSchema = {
  users,
  workspaces,
  workspaceMemberships,
  projects,
  stories,
  chapters,
  scenes,
  storyStates,
  storyStateDeltas,
  characters,
  characterRelationships,
  locations,
  worldRules,
  storyThreads,
  canonFacts,
  sceneDocuments,
  sceneVersions,
  generationRuns,
  aiUsage,
  outboxEvents,
  sceneCommitReceipts,
};
