# AI Short Story Platform V2 — Master Design Specification

## Status

Reviewed architecture approved after V1 red-team analysis. This document is the master source of truth; subsystem specs contain implementation detail.

## Goal

Build an AI Story Studio for creators that reliably generates and edits structured narration-ready fiction while maintaining narrative truth separately from prose.

## Product stages

1. **V0 Engine Proof** validates architecture against simpler baselines.
2. **V1 Alpha** ships a narrow, reliable creator workflow.
3. **V1 Beta** expands length/language/knowledge only after measured gates pass.

## V1 Alpha promise

- 3k–15k official story length;
- one optimized language;
- 2–3 optimized genres;
- one Standard quality mode;
- one-line idea + optional advanced setup;
- outline/scene planning;
- durable scene-by-scene generation;
- structured StoryState/Canon/Threads;
- Story Studio editing and contextual AI actions;
- manual-edit reconciliation;
- scene versioning/restore;
- TTS-ready text export.

## Architecture

```text
Next.js Web
   ↓ REST/SSE
NestJS API  ───── PostgreSQL + pgvector / Redis / ObjectStorage
   ↓ workflow gateway
Temporal
   ├── TypeScript workflow-worker
   └── Python ai-worker
          ↓
      Model/provider adapters
```

The API and workflow worker are separate processes. Python cannot directly commit domain truth.

## Story model

Story is not a long text blob. It contains planning, chapters/scenes, Bible entities, current StoryState, StateDelta history and structured SceneDocuments.

Scene is the primary generation/edit unit. V1 ScenePlan remains intentionally minimal.

## Truth model

- First-class domain entities own their own truth.
- CanonFact is used only where a richer entity does not already own the assertion.
- StoryState is the materialized current projection.
- State Extractor is the only AI component that proposes StoryDelta.
- Domain validation decides what becomes authoritative.

## Manual edits

A committed scene edit or restore can make structured state stale. Story exposes `consistencyStatus` and `dirtyFromSceneId`. Downstream generation cannot silently continue from dirty state; reconciliation re-extracts/validates state from the dirty boundary. Precise dependency repair is V1.5.

## Generation

`Intent → Architect → Plan → Scene loop(Context → Writer → Extractor → Validate → Commit) → bounded Story Critic → TTS polish`.

Deterministic validators handle hard invariants. Alpha avoids a sprawling multi-agent critic suite.

## Context/memory

Hard authority/current state/local narrative/long-term retrieval/project knowledge/writing profile are assembled under a budget. Summaries support narrative memory, never replace structured truth.

## AI/model routing

Story code calls capabilities. V1 routing is configured/static with provider adapters and bounded fallback. Dynamic routing/control-plane work waits for real usage/eval data.

## Knowledge

V1 Alpha uses user-supplied knowledge only. PostgreSQL FTS + pgvector is the baseline retrieval architecture. Web Research moves to V1.3.

## Workflow safety

Temporal carries IDs, versions and artifact references. Large contexts/scenes reside in product/artifact storage. All side effects are idempotent. Product progress is persisted in PostgreSQL and surfaced over REST/SSE.

## Persistence

PostgreSQL stores product truth, documents/versions, state/deltas, generation/usage and knowledge metadata. SceneDocument may be one JSONB structured payload with stable block IDs in V1. ObjectStorage is S3-compatible behind an interface.

## V1 exclusions

No Web Research, reference-derived Style Analyzer, adaptive router admin plane, automatic dependency repair, audio, CRDT, team UI, local serving, dedicated vector DB, Kubernetes or microservice extraction.

## Release quality

V0 and Alpha thresholds are defined in `specs/V0_ENGINE_PROOF.md` and `specs/ACCEPTANCE_AND_EVALS.md`. Architecture complexity must earn its cost through ablation and human preference tests.
