# Implementation status

## What is implemented

- Task 0 kickoff decisions are recorded under [`docs/adr`](docs/adr).
- Task 1 V0 harness lives under [`experiments/story-engine-v0`](experiments/story-engine-v0).
- Contracts cover `EvalCase`, `Premise`, `Blueprint`, `ScenePlan`,
  `SceneDocument`, `StoryState`, `StoryStateDelta`, usage, and eval results.
- Four variants are executable: Baseline A, Baseline B, Structured C, and
  Structured + lightweight QA D.
- The deterministic engine enforces the Writer/Extractor authority boundary,
  locked-canon validation, stable block IDs, sequential state commits, and
  version checks at the simulated domain boundary.
- Thirty Vietnamese evaluation cases cover the three selected genres, all three
  target-length bands, and continuity traps.
- An OpenRouter adapter and secret-safe smoke command are available. The first
  live pilot used `minimax/minimax-m3:free` and is recorded in
  [`experiments/story-engine-v0/results/LIVE-BENCHMARK-PILOT.md`](experiments/story-engine-v0/results/LIVE-BENCHMARK-PILOT.md).
- The adapter accepts two local keys, rotates round-robin per request, tries at
  most one alternate key after HTTP 429, and applies a cooldown while keeping
  key values out of diagnostics.
- Task 2 monorepo foundation is implemented at the repository root: canonical
  JSON Schemas, TypeScript/Python equivalents, process shells, and development
  Compose infrastructure.
- Task 3 authoritative Story domain is implemented under
  `apps/api/src/modules`: one-authority Story Bible rules, locked Canon checks,
  optimistic state/Canon version checks, idempotent validated scene commits,
  and dirty/reconciliation status transitions.
- Task 4 persistence core is implemented under
  `apps/api/src/infrastructure/database` and the owning document/story
  modules: Drizzle schema, SQL migration, PostgreSQL repositories, document
  base-revision checks, atomic scene-commit transaction boundary, transactional
  outbox receipt, and idempotency uniqueness.

## Verification

From `experiments/story-engine-v0`:

```powershell
$env:PYTHONPATH = "src"
python -m compileall -q src tests
python -m unittest discover -s tests -v
python -m story_v0.eval_runner --system all --output-dir results\v0-fixture
```

The offline result is documented in [`experiments/story-engine-v0/results/V0-GATE.md`](experiments/story-engine-v0/results/V0-GATE.md). The live pilot is not a
passing V0 gate: the free route rate-limited the structured multi-call path and
the model outputs were below the target length in the baseline pilot.

## Foundation verification

From the repository root:

```powershell
pnpm install
pnpm lint
pnpm test
pnpm typecheck
pnpm test:python
pnpm --filter @story-platform/api test:integration
```

The contract smoke test validates all eight fixtures against the canonical
schemas with Ajv. API and web health shells were exercised locally. Docker
Compose could not be executed on the implementation host because the Docker
CLI is not installed; the Compose file is intended for the local development
environment. Story domain tests pass with `pnpm --filter
@story-platform/api test`; persistence transaction/revision tests pass with
`pnpm --filter @story-platform/api test:integration`.

The persistence test suite currently exercises transaction semantics and
revision behavior without a live database. The PostgreSQL integration run is
pending on a host with Docker/PostgreSQL; `pnpm --filter
@story-platform/api db:migrate` is provided for that environment.

## Deferred gate

The live-provider benchmark and human V0 gate are still pending by explicit
development-sequencing decision recorded in
[`docs/adr/ADR-0022-benchmark-deferral.md`](docs/adr/ADR-0022-benchmark-deferral.md).
[`experiments/story-engine-v0/results/V0-GATE.md`](experiments/story-engine-v0/results/V0-GATE.md)
remains `NOT READY`; no Alpha release claim is made.

The remaining Task 4 gate is the live PostgreSQL integration run. After that,
the next implementation slice is Task 5: port the proven V0 AI capabilities
into the production Python worker.
