# Live benchmark pilot — OpenRouter

Status: **PILOT COMPLETE; V0 GATE STILL OPEN**

Configuration:

- Provider: OpenRouter.
- Model: `minimax/minimax-m3:free`.
- Case: `mystery-short-01` only.
- Variants attempted: Baseline A, Baseline B, Structured C, Structured + QA D.

The key was loaded from the local env file and was never written to source,
logs, or result artifacts.

## Connectivity

The secret-safe smoke request succeeded. It returned a five-character response
and one output token.

## Pilot observations

| Variant | Result | Observation |
| --- | --- | --- |
| Baseline A | Completed | 2,061 words for a 3,000-word target; 60.4s |
| Baseline B | Completed | 1,902 words for a 3,000-word target; 65.3s |
| Structured C | Failed | OpenRouter HTTP 429 during the structured path |
| Structured + QA D | Rejected | Model critic/validation did not accept the first scene |

The retry of Structured C in [`live-v0-c-retry`](live-v0-c-retry) received the
same HTTP 429. A subsequent run with the two-key pool in
[`live-v0-c-rotated`](live-v0-c-rotated) still completed zero scene commits
after 55.7s, so rotation did not yet produce a valid structured story. This is
evidence about the selected free route's availability under a multi-call
pipeline, not a model-quality conclusion.

Raw story artifacts and machine summaries are in
[`live-v0-pilot`](live-v0-pilot). Human paired evaluation has not started because
the pilot does not yet provide a valid complete C/D story pair.

## Decision

Do not declare the V0 gate passed and do not launch the 30-case run against the
same route without rate-limit handling or a higher-capacity provider/model.

Next live-benchmark requirements:

1. Keep bounded 429 handling that respects `Retry-After` and records rate-limit
   events without retry storms; the adapter now rotates at most once to a
   second configured key and applies cooldowns.
2. Use a provider/model capacity suitable for the multi-call Structured C/D
   pipeline, or schedule the free route in small batches with explicit pauses.
3. Run all 30 cases and retain the existing A/B/C/D contract and metrics.
4. Complete blind B-vs-C/D human scoring using the generated review form.
