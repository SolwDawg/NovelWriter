# AI Short Story Platform V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the structured Story Engine, then deliver a narrow V1 Alpha that generates, edits, reconciles, versions and exports coherent 3k–15k TTS-ready stories through durable workflows.

**Architecture:** Next.js is the product UI, NestJS is the product/domain API, a separate TypeScript process runs Temporal workflows/domain activities, Python runs AI capabilities, and PostgreSQL owns product truth. Large AI inputs/outputs are stored as artifacts and passed through Temporal by reference. Manual edits can mark a story dirty and must reconcile before downstream generation.

**Tech Stack:** Next.js, TypeScript, NestJS, Python, Temporal, PostgreSQL + pgvector, Redis, S3-compatible ObjectStorage, Docker Compose. Specific editor/ORM/auth/object-storage/provider choices are resolved by Task 0 and recorded as ADRs before dependent code is written.

**Spec:** `docs/superpowers/specs/2026-08-27-ai-short-story-platform-v2-design.md`

## Global Constraints

- V0 must pass before full V1 Alpha product implementation proceeds.
- V1 Alpha official story length is 3,000–15,000 words.
- V1 Alpha has one officially optimized language, 2–3 optimized genres and one Standard quality mode.
- Python AI workers never directly commit Story Canon/business truth.
- State Extractor is the only AI capability that proposes `StoryStateDelta`.
- Manual edits/restores can mark `Story.consistencyStatus=DIRTY`; downstream generation may not silently continue.
- API and TypeScript Temporal workflow-worker are separate runnable processes.
- Large ContextBundles/scenes are referenced by artifact ID/hash rather than carried in workflow state/history.
- Redis is not used as the durable story-generation orchestrator; BullMQ is not required in V1.
- Web Research, automatic dependency repair, style-reference analysis, audio, CRDT, local-LLM serving, Kubernetes and adaptive model-routing control plane are out of Alpha.
- Use TDD for deterministic behavior and separate evals for creative AI quality.

---

## Task 0: Resolve implementation kickoff decisions

**Files:**
- Create: `docs/adr/ADR-0016-alpha-language-genres.md`
- Create: `docs/adr/ADR-0017-editor.md`
- Create: `docs/adr/ADR-0018-data-access.md`
- Create: `docs/adr/ADR-0019-auth.md`
- Create: `docs/adr/ADR-0020-object-storage.md`
- Create: `docs/adr/ADR-0021-alpha-models.md`

**Interfaces:**
- Produces concrete choices consumed by later tasks: `ALPHA_LANGUAGE`, `ALPHA_GENRES`, editor package, ORM/data layer, auth implementation, ObjectStorage implementation and primary/fallback AI provider/model configuration.

- [ ] **Step 1: Run a one-page decision matrix for each choice**

Record two or three candidates, required criteria from `OPEN_DECISIONS.md`, operational constraints and the selected option. The decision file must include `Context`, `Decision`, `Consequences`, `Revisit trigger`.

- [ ] **Step 2: Lock Alpha evaluation scope**

Write exactly one optimized language and exactly 2–3 optimized genres into ADR-0016; do not leave a list of possibilities.

- [ ] **Step 3: Lock first AI benchmark configuration**

ADR-0021 must name the primary provider/model configuration and, if used, the fallback/structured-output model. Include current input/output cost assumptions and context limits used by V0.

- [ ] **Step 4: Commit**

```bash
git add docs/adr
git commit -m "docs: lock alpha implementation decisions"
```

---

## Task 1: Build the V0 engine evaluation harness

**Files:**
- Create: `experiments/story-engine-v0/pyproject.toml`
- Create: `experiments/story-engine-v0/src/story_v0/contracts.py`
- Create: `experiments/story-engine-v0/src/story_v0/baselines.py`
- Create: `experiments/story-engine-v0/src/story_v0/structured_engine.py`
- Create: `experiments/story-engine-v0/src/story_v0/eval_runner.py`
- Create: `experiments/story-engine-v0/src/story_v0/metrics.py`
- Create: `experiments/story-engine-v0/cases/`
- Test: `experiments/story-engine-v0/tests/`

**Interfaces:**
- Produces: `run_case(case: EvalCase, system: SystemVariant) -> EvalRunResult`.
- `SystemVariant` must support `BASELINE_A`, `BASELINE_B`, `STRUCTURED_C`, `STRUCTURED_QA_D`.

- [ ] **Step 1: Write failing contract tests**

```python
from story_v0.contracts import EvalCase, SystemVariant


def test_eval_case_requires_hard_constraints():
    case = EvalCase(
        id="mystery-001",
        premise="A taxi driver picks up a passenger who died ten years ago.",
        target_words=3000,
        genre="mystery",
        hard_constraints=["The passenger's identity stays secret until the final third."],
    )
    assert case.target_words == 3000
    assert SystemVariant.STRUCTURED_C.value == "structured_c"
```

- [ ] **Step 2: Run and verify failure**

```bash
cd experiments/story-engine-v0
uv run pytest tests -q
```

Expected: import/model failures because contracts do not exist.

- [ ] **Step 3: Implement minimal Pydantic/dataclass contracts and baseline runner interfaces**

Use explicit schemas for Premise, Blueprint, minimal ScenePlan, StoryState, StoryDelta and EvalRunResult. Do not add UI/product concerns.

- [ ] **Step 4: Add deterministic fake model tests**

Create a fake provider that returns fixture results so the structured loop can be tested without a live LLM.

- [ ] **Step 5: Add 30+ committed evaluation cases**

Cases must cover the chosen Alpha language/genres and continuity traps: relationship, inventory, knowledge, chronology, location and hidden reveal.

- [ ] **Step 6: Implement A/B/C/D variants**

C must run `Blueprint → ScenePlan → Writer → StateExtractor → Validator`. D adds only the bounded QA described by V0 spec.

- [ ] **Step 7: Emit machine-readable and human-review results**

Write JSONL/CSV summary with cost, latency, hard-constraint results and generated story paths; generate paired-review packets without revealing system identity.

- [ ] **Step 8: Run V0 benchmark and record gate decision**

Create `experiments/story-engine-v0/results/V0-GATE.md` with the exact thresholds from `specs/V0_ENGINE_PROOF.md`. If the gate fails, stop the full product implementation and iterate this task instead.

- [ ] **Step 9: Commit**

```bash
git add experiments/story-engine-v0
git commit -m "feat: prove structured story engine"
```

---

## Task 2: Scaffold the monorepo and shared contracts

> Execution note (2026-08-27): the V0 live-provider and human paired gate is
> explicitly deferred per ADR-0022 so foundation work can proceed. The V0 gate
> remains not ready for release claims.

**Files:**
- Create: `apps/web/`
- Create: `apps/api/`
- Create: `apps/workflow-worker/`
- Create: `services/ai-worker/`
- Create: `packages/contracts/`
- Create: `packages/domain-types/`
- Create: `infra/docker/compose.yml`
- Create: `pnpm-workspace.yaml`
- Create: root `package.json`, `README.md`, lint/test configs.

**Interfaces:**
- Canonical cross-runtime schemas live in `packages/contracts/schemas/`.
- Initial schemas: `StoryIntent`, `StoryBlueprint`, `ScenePlan`, `SceneDocumentArtifact`, `StoryState`, `StoryStateDelta`, `AIArtifactRef`, `AIUsage`.

- [x] **Step 1: Write contract generation smoke test**

The test must validate a fixture against the canonical JSON Schema and import the generated TypeScript/Python equivalent.

- [x] **Step 2: Scaffold apps/services without business features**

Each process exposes only a health check or worker startup command.

- [x] **Step 3: Add Docker infrastructure needed for the next vertical slice**

Start with PostgreSQL/pgvector and Temporal only if Task 4 needs them; Redis/ObjectStorage may be added when their first use appears. Do not create unused infrastructure merely because it exists in the future architecture.

- [x] **Step 4: Verify commands**

```bash
pnpm lint
pnpm test
uv run pytest services/ai-worker/tests -q
```

- [x] **Step 5: Commit**

```bash
git add .
git commit -m "chore: scaffold story platform monorepo"
```

---

## Task 3: Implement the authoritative Story domain and reconciliation rules

> Execution note (2026-08-27): implemented and pushed in commit `1bb9400`.

**Files:**
- Create: `apps/api/src/modules/story/domain/`
- Create: `apps/api/src/modules/story/application/`
- Create: `apps/api/src/modules/story-bible/domain/`
- Create: `apps/api/src/modules/document/domain/`
- Test: `apps/api/test/story-domain/`

**Interfaces:**

```ts
export type StoryConsistencyStatus = 'CLEAN' | 'DIRTY' | 'RECONCILING' | 'NEEDS_REVIEW';

export interface StoryRepository {
  get(storyId: string): Promise<Story>;
  save(story: Story, expectedVersion: number): Promise<void>;
}

export interface ApplyValidatedSceneCommand {
  storyId: string;
  sceneId: string;
  expectedStateVersion: number;
  expectedCanonVersion: number;
  documentArtifactId: string;
  delta: StoryStateDelta;
  idempotencyKey: string;
}
```

- [x] **Step 1: Write failing tests for one-authority invariants**

Test that a first-class relationship cannot also be mutated through an unrelated generic-fact write path.

- [x] **Step 2: Write failing tests for locked Canon and stale versions**

A locked fact mutation or stale state/canon commit must fail deterministically.

- [x] **Step 3: Write failing tests for dirty story semantics**

Editing/restoring a committed upstream scene must set `dirtyFromSceneId` to the earliest affected scene and block clean downstream generation until reconciliation.

- [x] **Step 4: Implement minimal domain entities/value objects/services**

Keep StoryState as a versioned materialized JSON-friendly projection plus StateDelta history. Do not create a normalized CharacterState history table yet.

- [x] **Step 5: Run domain tests**

```bash
pnpm --filter api test -- story-domain
```

- [x] **Step 6: Commit**

```bash
git add apps/api/src/modules/story apps/api/src/modules/story-bible apps/api/src/modules/document apps/api/test/story-domain
git commit -m "feat: add authoritative story domain and reconciliation rules"
```

---

## Task 4: Persist Story, SceneDocument, versions and atomic commits

**Files:**
- Create/modify per ADR-0018 under: `apps/api/src/infrastructure/database/`
- Create repository adapters under the owning modules.
- Create migrations for workspace/project/story/chapter/scene, StoryState/Delta, Bible entities, SceneDocument, SceneVersion, GenerationRun, AIUsage, Outbox.
- Test: `apps/api/test/persistence/`

**Interfaces:**
- Repositories from Task 3.
- `UnitOfWork.transaction(fn)` or selected equivalent.
- `SceneDocument` is persisted as structured JSONB with stable block IDs and a monotonically increasing revision.

- [ ] **Step 1: Write integration test for atomic scene commit**

Simulate a failure after document update but before state update and verify the transaction leaves neither partial write committed.

- [ ] **Step 2: Write optimistic-concurrency tests**

Stale `baseRevision`, story version and expected state/canon versions must fail with stable domain/application error codes.

- [ ] **Step 3: Implement repositories/migrations**

Use JSONB for evolving nested state/document payloads; relational columns for ownership/status/order/identity.

- [ ] **Step 4: Add transactional outbox and idempotency uniqueness**

Repeated commit activity with the same idempotency key returns the existing committed result.

- [ ] **Step 5: Run integration tests against PostgreSQL**

```bash
pnpm --filter api test:integration -- persistence
```

- [ ] **Step 6: Commit**

```bash
git add apps/api
git commit -m "feat: persist story state documents and versions"
```

---

## Task 5: Port the proven V0 AI capabilities into the production Python worker

**Files:**
- Create: `services/ai-worker/src/capabilities/intent/`
- Create: `services/ai-worker/src/capabilities/planning/`
- Create: `services/ai-worker/src/capabilities/scene_writer/`
- Create: `services/ai-worker/src/capabilities/state_extractor/`
- Create: `services/ai-worker/src/capabilities/critics/`
- Create: `services/ai-worker/src/model_router/`
- Create: `services/ai-worker/src/providers/`
- Create: `services/ai-worker/src/artifacts/`

**Interfaces:**

```python
class AIArtifactRef(BaseModel):
    artifact_id: str
    content_hash: str
    schema_version: int

async def generate_scene(request: SceneGenerationRequest) -> AIArtifactRef: ...
async def extract_story_delta(request: StateExtractionRequest) -> StoryStateDeltaResult: ...
```

- [ ] **Step 1: Copy eval fixtures, not experimental spaghetti**

Production capability contracts must be clean implementations informed by V0; do not import the V0 package as production runtime code unless an explicit extraction refactor makes it a supported shared library.

- [ ] **Step 2: Write fake-provider capability tests**

Verify writer returns a document artifact and **does not return an authoritative StoryDelta**. Verify State Extractor is the only capability that produces StoryDelta.

- [ ] **Step 3: Implement static routing config**

Read the provider/model choices from ADR-0021/config. Do not implement adaptive scoring.

- [ ] **Step 4: Implement artifact repository**

Persist large context/candidate content through the selected ObjectStorage/artifact implementation; return IDs/hashes.

- [ ] **Step 5: Add usage/latency/error metadata**

Every real model call returns normalized usage diagnostics.

- [ ] **Step 6: Run Python tests/eval regression subset**

```bash
uv run pytest services/ai-worker/tests -q
```

- [ ] **Step 7: Commit**

```bash
git add services/ai-worker packages/contracts
git commit -m "feat: add production ai capability runtime"
```

---

## Task 6: Deliver the first vertical story slice without the full editor

**Files:**
- Create API story/project modules/controllers needed for story creation/read.
- Create minimal web dashboard/story creation page.
- Create `apps/web/features/story-wizard/`.

**Interfaces:**
- `POST /api/v1/projects/:projectId/stories`.
- `GET /api/v1/stories/:storyId`.
- V1 wizard captures premise, target length, chosen genre/style preset and outline-review flag.

- [ ] **Step 1: Write API tests for create/read Story**
- [ ] **Step 2: Add authentication/workspace implementation selected in ADR-0019**
- [ ] **Step 3: Add minimal wizard UI and Story creation**
- [ ] **Step 4: Verify browser → NestJS → PostgreSQL happy path**
- [ ] **Step 5: Commit**

```bash
git add apps/web apps/api
git commit -m "feat: create stories from the web product shell"
```

---

## Task 7: Add Temporal durable generation as a separate workflow-worker process

**Files:**
- Create: `apps/workflow-worker/src/workflows/generate-story.workflow.ts`
- Create: `apps/workflow-worker/src/activities/`
- Create: `apps/workflow-worker/src/main.ts`
- Create: `services/ai-worker/src/temporal/worker.py`
- Create: `apps/api/src/modules/generation/`
- Create: `apps/api/src/modules/workflow-gateway/`

**Interfaces:**
- API `StartGenerationCommand` creates `GenerationRun` and calls `WorkflowGateway.start()`.
- Workflow passes only IDs/versions/artifact refs between steps.

- [ ] **Step 1: Write deterministic workflow test with fake activities**

Generate three scenes, each with its own commit activity, without any live LLM.

- [ ] **Step 2: Assert Temporal payload discipline**

Test workflow/activity result fixtures and reject/flag payloads containing full scene documents/ContextBundles above the documented artifact-reference threshold.

- [ ] **Step 3: Implement Python AI activities and NestJS/domain activities on separate task queues**
- [ ] **Step 4: Add pause/resume/cancel tests**
- [ ] **Step 5: Add transient failure and duplicate-commit idempotency tests**
- [ ] **Step 6: Add stale-context branch**
- [ ] **Step 7: Commit**

```bash
git add apps/workflow-worker apps/api/src/modules/generation apps/api/src/modules/workflow-gateway services/ai-worker/src/temporal
git commit -m "feat: generate stories with durable temporal workflows"
```

---

## Task 8: Add Story consistency reconciliation end to end

**Files:**
- Create: `apps/workflow-worker/src/workflows/reconcile-story.workflow.ts`
- Create: `apps/api/src/modules/story/application/reconcile-story.*`
- Add AI extraction activity/request to Python worker.
- Add API: `POST /api/v1/stories/:storyId/reconcile`.

**Interfaces:**
- `ReconcileStoryCommand(storyId, expectedStoryVersion)`.
- Workflow starts from `dirtyFromSceneId`, extracts/validates state sequentially and ends `CLEAN` or `NEEDS_REVIEW`.

- [ ] **Step 1: Write the canonical Lan-death scenario test from the reconciliation spec**
- [ ] **Step 2: Verify downstream generation refuses known-dirty story**
- [ ] **Step 3: Implement reconciliation workflow/state transitions**
- [ ] **Step 4: Add restore-version dirty semantics**
- [ ] **Step 5: Commit**

```bash
git add apps/api apps/workflow-worker services/ai-worker
git commit -m "feat: reconcile manual story edits with structured state"
```

---

## Task 9: Build the Story Studio editor vertical slice

**Files:**
- Create: `apps/web/features/story-editor/`
- Create: `apps/web/features/story-navigation/`
- Create: `apps/web/features/generation/`
- Create: `apps/web/features/story-consistency/`
- Add Document API endpoints under `apps/api`.

**Interfaces:**
- `GET /documents/:id`.
- `POST /documents/:id/changes` with `baseRevision`, `clientMutationId`, ordered operations.
- Story DTO includes `consistencyStatus`, `dirtyFromSceneId`.

- [ ] **Step 1: Implement the editor adapter selected by ADR-0017**
- [ ] **Step 2: Write UI tests for stable block IDs and ordered mutation queue**
- [ ] **Step 3: Implement Saved/Saving/Unsaved/Conflict states**
- [ ] **Step 4: Add three-panel shell and scene tree**
- [ ] **Step 5: Add explicit dirty/reconcile banner and actions**
- [ ] **Step 6: Connect generation progress through REST + SSE**
- [ ] **Step 7: Commit**

```bash
git add apps/web apps/api
git commit -m "feat: add structured story studio editor"
```

---

## Task 10: Add contextual AI editing and scene versions

**Files:**
- Create: `apps/web/features/ai-actions/`
- Create: `apps/web/features/versions/`
- Add registered AI action application handlers/workflow where needed.

**Interfaces:**
- `POST /scenes/:sceneId/ai-actions`.
- `GET /scenes/:sceneId/versions`.
- `POST /scenes/:sceneId/versions/:versionId/restore`.

- [ ] **Step 1: Write action-registry tests**

Only Alpha actions are registered: Rewrite, Expand, Shorten, Increase Tension, Improve Hook, TTS Polish, Regenerate Scene.

- [ ] **Step 2: Implement local proposal/accept/reject UX**
- [ ] **Step 3: Implement Regenerate Scene as immutable candidate/version**
- [ ] **Step 4: Write version-restore consistency test**

Restoring story-changing content marks/reconciles the story rather than mutating state silently.

- [ ] **Step 5: Commit**

```bash
git add apps/web apps/api apps/workflow-worker services/ai-worker
git commit -m "feat: add contextual ai editing and scene versions"
```

---

## Task 11: Add minimal Story Bible, writing profiles and export

**Files:**
- Create Story Bible panels/application resources.
- Create compact StyleProfile/GenreProfile/LanguageProfile implementation.
- Create export module/renderers.

**Interfaces:**
- Canon lock/unlock through domain commands.
- Alpha StyleProfile uses preset/tone/pacing/custom rules; no reference analyzer.
- Export current accepted story order to TXT/Markdown/DOCX.

- [ ] **Step 1: Write locked-fact UI/API integration test**
- [ ] **Step 2: Implement Characters/Relationships/World Rules/Canon/Threads creator views**
- [ ] **Step 3: Implement compact writing-profile resolver and trace its version in AI calls**
- [ ] **Step 4: Implement TXT/Markdown/DOCX export tests**
- [ ] **Step 5: Commit**

```bash
git add apps/web apps/api services/ai-worker
git commit -m "feat: add story bible profiles and export"
```

---

## Task 12: Add optional Alpha user-supplied knowledge after core generation is stable

**Files:**
- Create: `apps/api/src/modules/knowledge/`
- Create: `services/ai-worker/src/knowledge/`
- Add pgvector migration/index strategy.
- Create Knowledge panel only after backend tests pass.

**Interfaces:**
- Alpha inputs: pasted text/TXT/Markdown.
- `VectorStore.search(scope, query, limit)` abstraction.
- Baseline retrieval: project scope → FTS/vector candidates → simple merge/RRF.

- [ ] **Step 1: Write cross-workspace isolation test before retrieval implementation**
- [ ] **Step 2: Write prompt-injection boundary test**

A source containing “ignore system instructions” must be rendered as untrusted evidence and cannot change Canon/system authority.

- [ ] **Step 3: Implement minimal ingestion/chunk/embed/index path**
- [ ] **Step 4: Benchmark exact pgvector retrieval before adding ANN index**
- [ ] **Step 5: Add Knowledge panel and source enable/disable**
- [ ] **Step 6: Commit**

```bash
git add apps/api services/ai-worker apps/web
git commit -m "feat: add scoped user knowledge retrieval"
```

---

## Task 13: Release observability, privacy, backup and eval gates

**Files:**
- Create/modify observability config/packages.
- Create `evals/release/`.
- Create backup/restore runbook under `docs/operations/`.
- Add production log-redaction tests/config.

**Interfaces:**
- Trace IDs join Request → GenerationRun → Workflow → Capability → Artifact/Context IDs → Usage.
- Raw story/context logging is disabled by default.

- [ ] **Step 1: Implement usage/cost/latency metrics**
- [ ] **Step 2: Add log redaction/privacy test**
- [ ] **Step 3: Run deterministic release suite**

Required gates from `specs/ACCEPTANCE_AND_EVALS.md`: locked canon 100%, schema validity >=99%, extractor F1 >=0.95, scene outcome >=90%, no cross-workspace leakage.

- [ ] **Step 4: Run human eval sample and compare to V0 baseline**
- [ ] **Step 5: Execute one staging backup/restore drill and record result**
- [ ] **Step 6: Record actual cost per 10k words and decide Alpha release budget**
- [ ] **Step 7: Commit**

```bash
git add evals docs/operations packages apps services
git commit -m "test: enforce alpha quality reliability and privacy gates"
```

---

## Task 14: Alpha release and Beta decision

**Files:**
- Create: `docs/releases/V1-ALPHA-READINESS.md`
- Create: `docs/releases/V1-BETA-CANDIDATES.md`

**Interfaces:**
- Readiness document links exact test/eval/restore/cost evidence rather than subjective “looks good” statements.

- [ ] **Step 1: Verify every Alpha in-scope requirement maps to passing evidence**
- [ ] **Step 2: Verify every out-of-scope item remains absent or behind a disabled experimental flag**
- [ ] **Step 3: List Beta candidates by measured user pain/eval evidence, not by original roadmap order alone**
- [ ] **Step 4: Commit**

```bash
git add docs/releases
git commit -m "docs: record v1 alpha readiness and beta priorities"
```

---

## Self-review

### Spec coverage

- V0 engine proof: Task 1.
- Authoritative story/domain truth: Tasks 3–4.
- AI capabilities/static routing/artifacts: Task 5.
- Product shell vertical slice: Task 6.
- Separate Temporal worker and durable generation: Task 7.
- Manual-edit reconciliation: Task 8.
- Story Studio/autosave/progress: Task 9.
- AI actions/versioning: Task 10.
- Bible/profiles/export: Task 11.
- Minimal knowledge: Task 12.
- NFR/evals/backup/privacy: Task 13.
- Release gate: Task 14.

### Scope check

Web Research, dependency repair, style-reference analyzer, adaptive routing/admin control plane, audio, collaboration/local serving and scale infrastructure are intentionally not implemented by this plan.

### Type consistency

`StoryStateDelta` is produced only by State Extractor and applied only through NestJS domain/application commands. Large content uses `AIArtifactRef`. Story consistency status is shared by API/domain/frontend contracts.
