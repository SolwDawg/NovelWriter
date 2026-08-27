# V0 Story Engine Proof

## Purpose

Prove the core Story Engine is worth productizing before building the complete Story Studio and infrastructure surface.

V0 is a disposable-or-reusable engineering harness, not the commercial product.

## Hypothesis

A hierarchical scene-generation system with explicit story state should outperform simpler approaches on continuity and controllability enough to justify its additional cost and complexity.

## Baselines

Run the same story prompts through:

- **A — One-shot/long-form baseline:** one model request or the simplest provider-supported long generation.
- **B — Outline then long generation:** create outline, then generate large sections without explicit state reconciliation.
- **C — Structured engine:** blueprint → scene plans → scene generation → state extraction → validation.
- **D — Structured + lightweight QA:** C plus one Scene Critic/Story Critic where applicable.

If a provider cannot generate the full target in one request, Baseline A may use the simplest reasonable continuation strategy; document it explicitly.

## V0 scope

- Python CLI/test harness.
- One primary language.
- 2–3 genres.
- Test story lengths around 3k, 10k and 15k.
- One primary model/provider configuration, optionally one secondary model for extraction/critique if needed.
- Premise/Blueprint/ScenePlan.
- Simple structured StoryState.
- State Extractor.
- Locked Canon validation.
- Open Threads.
- Scene summaries/context assembly.
- Cost/latency logging.
- Human-evaluation export package.

No auth, web app, editor, Temporal, billing, Web Research or RAG is required for V0.

## Required dataset

Create at least 30 evaluation prompts before judging the engine:

- 10 short ~3k targets.
- 10 medium ~10k targets.
- 10 long ~15k targets.
- Coverage across the selected genres.
- Synthetic continuity traps: inventory, relationships, character knowledge, chronology, location and secret reveals.

The prompts and expected hard constraints become persistent eval fixtures.

## Metrics

### Deterministic
- locked-canon violations;
- required scene-outcome adherence;
- invalid structured outputs;
- state-extraction precision/recall/F1 on annotated subsets;
- unresolved critical story threads;
- word-count error;
- cost and latency.

### Human rubric, 1–5
- coherence;
- engagement;
- character consistency;
- payoff/ending satisfaction;
- TTS readability;
- perceived repetition.

## V0 pass gate

Proceed to V1 Alpha if either condition is met:

1. Structured engine wins human preference against Baseline B on at least **65%** of paired comparisons while keeping cost within the agreed multiplier; or
2. It delivers a clearly superior deterministic continuity score and the team explicitly accepts a weaker human-preference margin because the controllability/versioning product strategy depends on structured state.

Additionally:
- locked-canon test pass = 100%;
- structured-output validity after bounded repair >= 99%;
- state-extractor F1 on annotated facts >= 0.95;
- no critical architecture defect requiring a different state model.

If these gates fail, improve or simplify the engine before building the full product shell.
