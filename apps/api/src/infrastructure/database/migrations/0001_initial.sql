-- NovelWriter persistence baseline.
-- Product truth lives in PostgreSQL; Temporal receives IDs and artifact refs.
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
  id text PRIMARY KEY,
  email text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workspaces (
  id text PRIMARY KEY,
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workspace_memberships (
  id text PRIMARY KEY,
  workspace_id text NOT NULL REFERENCES workspaces(id),
  user_id text NOT NULL REFERENCES users(id),
  role text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, user_id)
);

CREATE TABLE IF NOT EXISTS projects (
  id text PRIMARY KEY,
  workspace_id text NOT NULL REFERENCES workspaces(id),
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stories (
  id text PRIMARY KEY,
  project_id text NOT NULL REFERENCES projects(id),
  title text NOT NULL,
  status text NOT NULL CHECK (status IN ('DRAFT', 'GENERATING', 'COMPLETE')),
  target_word_count integer NOT NULL CHECK (target_word_count BETWEEN 3000 AND 15000),
  language text NOT NULL,
  genre text NOT NULL CHECK (genre IN ('Mystery', 'Thriller', 'Horror')),
  output_mode text NOT NULL CHECK (output_mode = 'standard'),
  intent_json jsonb NOT NULL CHECK (jsonb_typeof(intent_json) = 'object'),
  blueprint_json jsonb,
  current_state_version integer NOT NULL DEFAULT 0 CHECK (current_state_version >= 0),
  canon_version integer NOT NULL DEFAULT 1 CHECK (canon_version >= 1),
  consistency_status text NOT NULL CHECK (
    consistency_status IN ('CLEAN', 'DIRTY', 'RECONCILING', 'NEEDS_REVIEW')
  ),
  dirty_from_scene_id text,
  version integer NOT NULL DEFAULT 0 CHECK (version >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS stories_project_idx ON stories(project_id);

CREATE TABLE IF NOT EXISTS chapters (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  title text NOT NULL,
  ordinal integer NOT NULL CHECK (ordinal >= 1),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (story_id, ordinal)
);

CREATE TABLE IF NOT EXISTS scenes (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  chapter_id text REFERENCES chapters(id),
  ordinal integer NOT NULL CHECK (ordinal >= 1),
  status text NOT NULL,
  current_document_revision integer NOT NULL DEFAULT 0 CHECK (current_document_revision >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (story_id, ordinal)
);

CREATE INDEX IF NOT EXISTS scenes_story_idx ON scenes(story_id);

CREATE TABLE IF NOT EXISTS story_states (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  version integer NOT NULL CHECK (version >= 0),
  state_json jsonb NOT NULL CHECK (jsonb_typeof(state_json) = 'object'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (story_id, version)
);

CREATE TABLE IF NOT EXISTS story_state_deltas (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  scene_id text NOT NULL REFERENCES scenes(id),
  state_version integer NOT NULL CHECK (state_version >= 1),
  delta_json jsonb NOT NULL CHECK (jsonb_typeof(delta_json) = 'object'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (story_id, scene_id)
);

CREATE TABLE IF NOT EXISTS characters (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  name text NOT NULL,
  profile_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS character_relationships (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  subject_character_id text NOT NULL REFERENCES characters(id),
  relation_type text NOT NULL,
  object_character_id text NOT NULL REFERENCES characters(id),
  source text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (story_id, subject_character_id, relation_type, object_character_id)
);

CREATE TABLE IF NOT EXISTS locations (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  name text NOT NULL,
  metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS world_rules (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  rule_text text NOT NULL,
  locked boolean NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS story_threads (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  title text NOT NULL,
  status text NOT NULL CHECK (status IN ('OPEN', 'ADVANCING', 'RESOLVED', 'DROPPED')),
  metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS canon_facts (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  subject_ref text NOT NULL,
  predicate text NOT NULL,
  value_json jsonb NOT NULL,
  locked boolean NOT NULL,
  source text NOT NULL,
  introduced_scene_id text REFERENCES scenes(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS canon_facts_lookup_idx
  ON canon_facts(story_id, subject_ref, predicate);

CREATE TABLE IF NOT EXISTS scene_documents (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  scene_id text NOT NULL REFERENCES scenes(id),
  artifact_id text,
  revision integer NOT NULL CHECK (revision >= 1),
  document_json jsonb NOT NULL CHECK (jsonb_typeof(document_json) = 'object'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (scene_id)
);

CREATE TABLE IF NOT EXISTS scene_versions (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  scene_id text NOT NULL REFERENCES scenes(id),
  revision integer NOT NULL CHECK (revision >= 1),
  source text NOT NULL CHECK (source IN ('MANUAL', 'AI', 'REGENERATE', 'RESTORE')),
  document_json jsonb NOT NULL CHECK (jsonb_typeof(document_json) = 'object'),
  metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (scene_id, revision)
);

CREATE TABLE IF NOT EXISTS generation_runs (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  status text NOT NULL,
  idempotency_key text,
  metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (story_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS ai_usage (
  id text PRIMARY KEY,
  story_id text NOT NULL REFERENCES stories(id),
  generation_run_id text REFERENCES generation_runs(id),
  provider text NOT NULL,
  model text NOT NULL,
  input_tokens integer NOT NULL CHECK (input_tokens >= 0),
  output_tokens integer NOT NULL CHECK (output_tokens >= 0),
  total_tokens integer NOT NULL CHECK (total_tokens >= 0),
  estimated_cost_usd numeric(18, 8) NOT NULL CHECK (estimated_cost_usd >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scene_commit_receipts (
  id text PRIMARY KEY,
  idempotency_key text NOT NULL UNIQUE,
  story_id text NOT NULL REFERENCES stories(id),
  scene_id text NOT NULL REFERENCES scenes(id),
  document_revision integer NOT NULL CHECK (document_revision >= 1),
  resulting_state_version integer NOT NULL CHECK (resulting_state_version >= 1),
  resulting_story_version integer NOT NULL CHECK (resulting_story_version >= 1),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS outbox_events (
  id text PRIMARY KEY,
  aggregate_type text NOT NULL,
  aggregate_id text NOT NULL,
  event_type text NOT NULL,
  idempotency_key text NOT NULL UNIQUE,
  payload_json jsonb NOT NULL CHECK (jsonb_typeof(payload_json) = 'object'),
  published_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS outbox_events_pending_idx
  ON outbox_events(created_at)
  WHERE published_at IS NULL;

COMMIT;
