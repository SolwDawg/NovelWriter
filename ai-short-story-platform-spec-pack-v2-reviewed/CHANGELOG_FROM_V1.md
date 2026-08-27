# Changelog from V1 to V2 Reviewed

## Scope changes

- Added mandatory **V0 Engine Proof** before full Alpha build.
- V1 Alpha official length changed from 3k–30k to **3k–15k**; 15k–30k moves to Beta quality gate.
- V1 Alpha changes from 2–3 optimized languages to **one optimized language**.
- V1 Alpha changes from 3–5 genres to **2–3 optimized genres**.
- V1 Alpha exposes **Standard** quality mode only; Fast/High Quality move to Beta after measurements.
- **Web Research** moved to V1.3.
- **Reference-derived Style Analyzer** moved to V1.2.
- **Dependency graph / impact analysis / automatic downstream repair** moved to V1.5.
- Full adaptive Model Router admin/control plane removed from Alpha.
- BullMQ removed as a V1 requirement.

## Architecture corrections

- Added `StoryConsistencyStatus` and `dirtyFromSceneId`.
- Added explicit `ReconcileStoryWorkflow` for manual edits/restores.
- Defined a one-authority rule to prevent duplicate writable story truth.
- State Extractor is now the only AI capability producing `StoryStateDelta`.
- ScenePlan core contract is smaller; rich details are optional metadata.
- V1 StoryState is a materialized projection + deltas; normalized CharacterState history is deferred until justified.
- SceneDocument may be persisted as structured JSONB snapshot in V1 rather than one row per block.
- Temporal workflow state uses artifact references for large AI input/output.
- TypeScript workflow worker is a separate process from NestJS HTTP API.
- S3-compatible ObjectStorage remains locked; concrete implementation is reopened.
- RAG baseline simplified to project scope + FTS + pgvector + simple merge/RRF.

## Quality/process changes

- Added architecture ablation against simple baselines.
- Added explicit Alpha release thresholds for schema validity, extractor F1, scene-outcome adherence and zero cross-workspace retrieval leakage.
- Added prompt-injection boundary for uploaded/retrieved content.
- Added privacy rule: raw unpublished story/context content is not logged by default.
- Added backup/restore requirements and restore drill.
- Rewrote implementation plan from horizontal infrastructure phases to vertical slices.
