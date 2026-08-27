# Red-Team Review of V1

## Executive conclusion

The original architecture was directionally strong, but the original MVP scope mixed core V1 features with V1.2–V1.5 capabilities. The reviewed design keeps the architectural seams while cutting implementation burden by roughly one third to one half.

## What remains strong

The following decisions survived review unchanged in principle:

- hierarchical, scene-based generation;
- structured Story State and Canon;
- Story Engine separated from the TTS renderer;
- NestJS owns product/domain rules;
- Python owns AI computation, not business truth;
- Temporal owns orchestration, not product truth;
- PostgreSQL owns authoritative product state;
- RAG is supporting evidence, never canonical story memory;
- stable scene/block identities enable targeted editing and later TTS/audio mapping;
- model providers remain behind capability/provider interfaces.

## Problems found in V1

### 1. Scope leakage

Dependency-aware downstream repair, deep Web Research, reference-derived Style Analyzer, multi-pass specialized critics, three quality tiers and a full model-admin control plane were described as MVP even though the roadmap positioned several of them later.

**Correction:** V1 Alpha now exposes one Standard quality mode, no Web Research, no automatic dependency repair and no Style Reference Analyzer.

### 2. Manual-edit consistency hole

A user could manually change a story-critical event in prose while Canon/StoryState remained unchanged. Version restoration had the same problem.

**Correction:** scene edits can mark the story `DIRTY_FROM_SCENE`. Before downstream AI generation, the system reconciles the edited scene into a validated Story Delta and rebuilds state from the dirty boundary.

### 3. Multiple apparent sources of truth

Relationship, CanonFact, CharacterState, StoryState and other objects could duplicate the same fact.

**Correction:** each fact has one authoritative owner. Derived representations are read projections. `CanonFact` is not a universal EAV replacement for first-class domain entities.

### 4. Excessively detailed ScenePlan

The original required many fields even when they were unnecessary, increasing token cost and reducing creative flexibility.

**Correction:** V1 requires only purpose, POV/location/participants where relevant, required outcome, required facts, forbidden reveals, active threads, target tension and target length. Additional planning data is optional metadata.

### 5. Writer/Extractor duplication

The Scene Writer and State Extractor both proposed state changes.

**Correction:** only the State Extractor produces `ProposedStoryDelta`. Writer output is prose/document plus diagnostics.

### 6. QA explosion

Too many specialized LLM critics would make V1 slow and expensive.

**Correction:** deterministic validators cover structured invariants; V1 uses a Scene Critic and Story Critic. Specialized critic services are added only when evals prove value.

### 7. Model Router over-implementation

Dynamic scoring, adaptive routing and admin controls were premature.

**Correction:** keep the Router contract, implement a static configuration policy in V1, collect data, and add adaptive routing later.

### 8. Research feature creep

Web Research added browsing, trust, provenance, security and provider complexity without being core to the first product promise.

**Correction:** V1 supports user-supplied knowledge only. Web Research moves to V1.3.

### 9. Temporal payload risk

Large ContextBundles and generated scenes could have ended up in workflow history.

**Correction:** use an artifact-reference/claim-check pattern. Workflow history carries small IDs, hashes, versions and status metadata. Large AI inputs/outputs live in product/artifact storage.

### 10. Process coupling

The original monorepo description risked running the Temporal TypeScript worker inside the API process.

**Correction:** `api` and `workflow-worker` are separate processes/containers.

### 11. Unnecessary queue technology

BullMQ duplicated part of Temporal's background-job role.

**Correction:** Redis remains for cache/rate-limit/realtime support; V1 does not require BullMQ.

### 12. Object-storage implementation was over-locked

The abstraction was correct but the implementation should remain replaceable.

**Correction:** keep `ObjectStorage`; select the S3-compatible implementation during infrastructure kickoff.

### 13. Retrieval over-design

RAG had query understanding, reranking and compression before baseline retrieval was measured.

**Correction:** V1 uses project scoping + PostgreSQL FTS + pgvector + reciprocal-rank fusion or a similarly simple merge. Add reranking/compression based on evals.

### 14. Release promises too broad

Thirty-thousand-word stories, multiple optimized languages, multiple quality tiers and 3–5 genres multiplied the evaluation matrix.

**Correction:** V1 Alpha officially supports 3k–15k, one primary optimized language, 2–3 optimized genres and one Standard quality mode. Longer stories and more languages are Beta gates.

## Result

V2 follows the rule: **keep architecture, reduce implementation**.
