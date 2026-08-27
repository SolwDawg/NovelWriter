# ADR-0021: Initial V0 model configuration

## Context

The V2 plan requires deterministic fake providers before live-model workflow
tests. This workspace has no API credentials or installed AI runtime, so a live
provider cannot be benchmarked honestly during the first implementation slice.

## Decision

The initial V0 live benchmark configuration is now:

```yaml
primary:
  provider: openrouter
  model: minimax/minimax-m3:free
fallback:
  provider: fixture
  model: deterministic-repair-v0
```

The offline deterministic provider remains the regression fallback and is not
silently mixed into live quality results. The provider endpoint is
`https://openrouter.ai/api/v1/chat/completions`; the key is loaded from local
environment configuration only.

The initial offline configuration remains:

```yaml
primary:
  provider: fixture
  model: deterministic-story-v0
fallback:
  provider: fixture
  model: deterministic-repair-v0
capabilities:
  planner: primary
  scene_writer: primary
  state_extractor: primary
  critics: fallback
```

The selected `:free` route is assumed to have `$0.00` provider cost during this
benchmark, but availability, rate limits, output limits, and quality are not
guaranteed. The harness records actual input/output tokens, elapsed time, and
provider errors. No cloud model is considered Alpha-release approved by this
ADR; a later revision must record measured context limits, cost envelope,
fallback behavior, and quality results.

## Consequences

Contract, state, validation, artifact-reference, and evaluation logic can be
tested offline while the OpenRouter route supplies the first live benchmark.
Human preference and the complete live-model quality gate remain pending, so a
successful connectivity check cannot by itself declare the V0 gate passed.

## Revisit trigger

Revisit before Task 5 production AI integration or any Alpha release decision,
and whenever provider/model/prompt changes affect quality, cost, or context
limits.
