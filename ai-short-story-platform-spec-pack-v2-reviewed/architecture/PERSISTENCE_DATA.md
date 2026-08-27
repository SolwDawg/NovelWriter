# Persistence & Data Architecture V2

## 1. Ownership

- PostgreSQL: authoritative product state.
- ObjectStorage: uploads, exports and large AI artifacts.
- Temporal: execution history/state.
- Redis: ephemeral/cache/rate-limit/realtime support.

## 2. Relational entities

Expected core tables/aggregates include:
- users/workspaces/workspace_memberships;
- projects/stories;
- chapters/scenes;
- characters/relationships/locations/world_rules/story_threads;
- canon_facts where appropriate;
- story_states/story_state_deltas;
- scene_documents;
- scene_versions/story_snapshots;
- style/genre/language profile metadata;
- generation_runs/ai_usage;
- knowledge_sources/knowledge_chunks/embeddings if Alpha knowledge enabled;
- outbox_events.

## 3. JSONB policy

Use relational columns for identity, ownership, status, ordering, filtering and join-heavy fields. Use versioned JSONB for nested evolving payloads such as StoryState, ScenePlan optional metadata, SceneDocument and profile details.

## 4. Scene document persistence

V1 may store a scene's structured document as one JSONB payload with stable block IDs rather than one DB row per block. Autosave sends operations/patches and server applies them against a document revision.

This keeps the editor model structured without premature row-level fragmentation.

## 5. State history

`story_states` stores materialized current/checkpoint states; `story_state_deltas` stores accepted transitions. Do not require a separate CharacterState history table until query/performance requirements justify the projection.

## 6. Versioning

SceneVersion is immutable and snapshots the accepted document/planning references. Diff is calculated on demand in V1.

## 7. Atomic scene commit

A validated commit transaction can:
- create/update SceneDocument;
- create immutable SceneVersion when required;
- persist accepted StateDelta/new StoryState;
- update story version/consistency projections;
- write usage/generation records;
- write outbox event.

AI calls happen before this short transaction.

## 8. Optimistic concurrency

Document saves use `baseRevision`. Story/Canon/State commits use expected versions. Stale operations fail/reconcile rather than overwrite silently.

## 9. Outbox/idempotency

Use transactional outbox for domain events. Side-effect consumers and workflow activities use idempotency keys/unique constraints.

## 10. AI artifacts

Large ContextBundles and AI candidate documents may be stored in an artifact repository backed by ObjectStorage or a controlled DB/object combination. Temporal receives only artifact IDs/hashes and small metadata.

## 11. Embeddings

Embedding records include model/profile version. V1 starts with exact pgvector search where viable and adds ANN only after dataset/latency measurements.

## 12. Delete/purge

Soft-delete for recoverable product UX is separate from hard purge. Purge removes authoritative DB records, vectors and object artifacts per retention policy.
