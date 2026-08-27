# V0 Gate — initial deterministic fixture run

Status: **NOT READY FOR V1 ALPHA**

The first implementation slice is a dependency-free deterministic harness. It
proves that the contracts and state boundary are executable, but it is not a
live-model or human-preference result. Per the reviewed specs, the product shell
must not be treated as Alpha-ready until the V0 gate is completed.

## Run

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m story_v0.eval_runner --system all --output-dir results\v0-fixture
```

The machine-readable output is in [`v0-fixture`](v0-fixture), including
`summary.jsonl`, `summary.csv`, `aggregate.json`, generated stories, and a
blinded review packet.

## Fixture health results

The run used 30 cases: 10 at 3,000 words, 10 at 10,000 words, and 10 at 15,000
words across Mystery, Thriller, and Horror.

| Variant | Required outcome rate | Locked canon pass | Schema valid | Extractor F1 |
| --- | ---: | ---: | ---: | ---: |
| Baseline A | 0% | 100% | 100% | 0.00 |
| Baseline B | 50% | 100% | 100% | 0.00 |
| Structured C | 100% | 100% | 100% | 1.00 |
| Structured + QA D | 100% | 100% | 100% | 1.00 |

These numbers are expected fixture behavior, not evidence of live model quality.

## Why the gate remains open

- The primary/fallback configuration is the local `fixture` provider, so model
  cost and latency are not production estimates.
- The required blind human preference comparison against Baseline B has not
  been performed.
- A live provider/model, prompt/schema versions, and real token-cost envelope
  must be benchmarked before Alpha release.

## Next gate actions

1. Keep the fixture suite as deterministic regression coverage.
2. Add a provider adapter that emits the same contracts and records normalized
   usage/error metadata.
3. Run the 30 cases through A/B/C/D with a real model configuration.
4. Complete blind human scoring for coherence, engagement, consistency, ending,
   TTS readability, and repetition.
5. Record the final threshold decision before starting the full Alpha shell.

