# Acceptance Tests & AI Evaluation — V2

## 1. Deterministic Alpha release gates

The following are hard pass/fail gates unless explicitly revised in an ADR.

### Workflow
- generation request returns ID without a long held request;
- at least three scenes commit independently;
- pause/resume continues from the next valid boundary;
- cancel preserves committed scenes;
- transient retry creates no duplicate committed scene version;
- stale state/canon versions cannot commit silently.

### Canon/domain
- locked-canon deterministic test pass: **100%**;
- domain idempotency tests: **100%**;
- duplicate authoritative representations cannot be written through two independent APIs.

### Manual edit reconciliation
- edit a committed scene to change a story-critical fact;
- verify `DIRTY_FROM_SCENE`/equivalent status;
- verify downstream generation is blocked or reconciled rather than silently using stale state;
- reconcile, validate and continue with the new state;
- restore an old scene version and verify the same consistency behavior.

### Document/versioning
- stale base revision returns conflict;
- autosave does not replace the entire story;
- scene versions remain immutable;
- restored version is reproducible.

### Knowledge/security
- cross-workspace retrieval leakage: **0 successful leak cases** in the test suite;
- untrusted retrieved instructions cannot override system/canon authority in prompt/context construction tests.

## 2. AI structured-output gates

- JSON/schema validity after bounded repair >= **99%** on the release eval set.
- State Extractor fact F1 >= **0.95** on annotated controlled cases.
- Locked-canon adherence in generated/validated paths = **100% committed-output compliance**.
- Required scene-outcome adherence >= **90%** on controlled scene fixtures.
- Target story length within **±10%** for at least 90% of release evaluation stories, unless genre-specific exceptions are approved.

## 3. Human quality rubric

Rate 1–5:
- coherence;
- engagement;
- character consistency;
- payoff/ending quality;
- TTS readability;
- repetition fatigue.

Use blind paired comparison where possible.

## 4. V0 architecture ablation

Compare:
- A: simplest long generation;
- B: outline + simple generation;
- C: structured state engine;
- D: structured state + lightweight QA.

Track quality, continuity, cost, latency and human preference. Architecture complexity must earn its cost.

## 5. Model/prompt release policy

For every provider/model/prompt change affecting generation, run the relevant eval slice and record:
- model/provider;
- prompt/schema version;
- language/genre;
- acceptance rate;
- repair rate;
- latency;
- input/output token cost;
- human preference where applicable.

Do not ship a regression in hard constraints or structured validity in exchange for creative preference without explicit approval.

## 6. Beta gates

Before officially supporting 15k–30k or a second language, create dedicated eval sets and require equivalent deterministic gates plus a human review sample large enough to expose long-range continuity drift.
