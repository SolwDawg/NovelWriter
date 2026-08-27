# AI Short Story Platform — Spec Pack V2 Reviewed

Version: **2.0 reviewed**  
Review date: **2026-08-27**

This package replaces the original V1 package as the recommended implementation source of truth. V1 remains useful as design history, but V2 incorporates a full red-team review focused on scope discipline, data consistency, Temporal payload safety, AI evaluation and vertical delivery.

## Product thesis

Build a web-based AI Story Studio that is simple by default for content creators and deep enough for serious writers. The system is TTS-first but output-neutral, scene-first rather than one-shot, and maintains structured story truth separately from generated prose.

The core product advantage is not “better prompting.” It is controlled long-form generation:

`Idea → Blueprint → Scene Plans → Scene Generation → State Reconciliation → Validation → Commit → Revision`

## Version strategy

- **V0 Engine Proof** — prove the hierarchical engine beats simpler baselines before investing in the full product shell.
- **V1 Alpha** — one production-quality creator flow with durable story generation and editing.
- **V1 Beta** — broaden length/language/knowledge support after Alpha quality gates pass.
- **V1.2** — creator productivity and reference-derived styles.
- **V1.3** — Web Research and stronger knowledge workflows.
- **V1.5** — structural story intelligence: dependency graph, impact analysis and downstream repair.
- **V2+** — multi-output/prose, audio, professional writer tooling, collaboration and local/private AI.

## Locked architecture boundaries

- Frontend: Next.js; Story Studio is client-heavy.
- Product/domain API: NestJS modular monolith.
- Temporal workflow worker: separate process from the HTTP API, using shared TypeScript application/domain code.
- AI compute: Python workers.
- Durable orchestration: Temporal.
- Product truth: PostgreSQL + pgvector.
- Cache/rate limits/realtime fanout: Redis. **BullMQ is not required in V1.**
- Object storage: S3-compatible abstraction; implementation is intentionally open.
- Story content: structured scene document with stable block IDs; V1 persistence may use JSONB snapshots.
- Knowledge: Story Canon, Lore, Research and Style References remain distinct.
- AI: capability-based model abstraction; V1 routing is deliberately simple/static.
- Collaboration: single-user V1, collaboration-ready boundaries only.

## Five post-review corrections that are mandatory

1. Manual prose edits and restored scene versions can invalidate Story State; V2 adds explicit **Story Consistency/Reconciliation**.
2. Domain truth has one authoritative write path; duplicate representations are projections, not independent writable truths.
3. Large prose/context payloads do not travel through Temporal history; workflows pass IDs, versions and artifact references.
4. API process and Temporal workflow-worker process are operationally separate.
5. Delivery is vertical-slice based and begins with V0 engine proof, not with a long horizontal infrastructure build.

## Documents

- `RED_TEAM_REVIEW.md` — why V1 was changed.
- `interview/PRODUCT_INTERVIEW_V2.md` — consolidated interview plus reviewed decisions.
- `specs/PRD.md` — product requirements.
- `specs/V0_ENGINE_PROOF.md` — pre-product engine validation.
- `specs/MVP_SCOPE.md` — V1 Alpha scope.
- `specs/V1_BETA_SCOPE.md` — Beta expansion.
- `specs/NON_FUNCTIONAL_REQUIREMENTS.md` — reliability, privacy, security and operational requirements.
- `specs/ACCEPTANCE_AND_EVALS.md` — deterministic release gates and AI evals.
- `architecture/*` — system and subsystem specifications.
- `roadmap/VERSIONS_ROADMAP.md` — revised product roadmap.
- `docs/superpowers/specs/2026-08-27-ai-short-story-platform-v2-design.md` — master design spec.
- `docs/superpowers/plans/2026-08-27-ai-short-story-platform-v2-plan.md` — vertical implementation plan.
- `OPEN_DECISIONS.md` — choices intentionally left to kickoff/benchmarking.
- `CODEX_HANDOFF.md` — implementation-agent instructions.
