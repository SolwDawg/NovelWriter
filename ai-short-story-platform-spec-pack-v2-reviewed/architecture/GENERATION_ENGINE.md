# Generation Engine V2

## 1. Standard V1 pipeline

```text
Idea
→ Intent Interpreter
→ Story Architect
→ Blueprint Validation
→ Chapter/Scene Planning
→ for each scene:
     build context artifact
     generate scene artifact
     extract ProposedStoryDelta
     deterministic/domain validation
     lightweight Scene Critic when configured
     targeted repair if needed
     atomic Scene + State commit
→ Story Critic
→ bounded final revision
→ TTS Polish
→ First Draft snapshot
```

## 2. Writer/Extractor authority

Scene Writer returns:
- structured SceneDocument artifact;
- usage/generation diagnostics;
- optional non-authoritative hints.

**Scene Writer does not author StoryDelta.**

State Extractor is the single AI capability that proposes `StoryStateDelta` from the candidate scene and prior valid state.

## 3. Minimal ScenePlan

Required:
- purpose;
- required outcome;
- required facts;
- forbidden reveals;
- active threads;
- target tension/length;
- POV/location/participants where relevant.

Optional planning detail is metadata. Do not force every genre/scene into the same over-specified schema.

## 4. Context

Context Builder selects hard constraints, current state, local narrative memory, relevant threads/canon, optional project knowledge and writing profile under a per-capability budget.

Large ContextBundle content is written to an artifact store; workflow passes an artifact reference.

## 5. Validation

Prefer deterministic checks for structured invariants:
- locked canon;
- expected state/canon versions;
- required outcome/fact presence where mechanically representable;
- thread/state transitions;
- word-count bounds;
- schema correctness.

Use AI critics for qualitative issues such as awkward pacing, repetition or weak narrative clarity.

## 6. Atomic commit

After validation, NestJS domain activity atomically:
- writes accepted SceneDocument/current version;
- creates immutable SceneVersion as required;
- applies accepted StateDelta;
- updates StoryState/current versions;
- updates thread/domain projections;
- writes usage/generation metadata and outbox events.

No LLM/network call occurs inside the DB transaction.

## 7. Repair policy

- infrastructure errors: retry/fallback according to provider policy;
- invalid structured output: bounded schema repair/retry;
- canon/state conflict: targeted rewrite or reject candidate;
- low qualitative score: targeted revision before full regeneration where practical;
- stale context: rebuild from current valid state, do not blind-retry commit.

## 8. Story-level QA

V1 uses a bounded Story Critic plus deterministic thread/canon checks. Specialized Canon/Timeline/Arc/Foreshadowing agents are not mandatory Alpha components.

## 9. Quality modes

V1 Alpha UI exposes only `Standard`.

The internal policy shape remains quality-tier capable so Beta can add Fast/High Quality after cost/quality evals. Do not maintain three unproven pipelines in Alpha.

## 10. Manual editing

Before generation, check Story consistency. If dirty, run reconciliation described in `STORY_CONSISTENCY_RECONCILIATION.md`.

## 11. Core invariant

```text
Prose candidate
→ State Extractor
→ Proposed Delta
→ Domain validation
→ Commit
```

Text alone is never authoritative truth.
