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

## Intentionally not started yet

The live-provider benchmark and human V0 gate are still pending. Therefore the
NestJS/Next.js/Temporal/PostgreSQL production shell has not been built yet; this
follows the spec's rule that V0 proof precedes full Alpha investment.
