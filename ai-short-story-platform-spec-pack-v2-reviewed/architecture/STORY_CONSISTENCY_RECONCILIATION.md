# Story Consistency & Manual Edit Reconciliation V1

## 1. Problem

Story prose and structured StoryState can diverge when a user:
- manually edits a committed scene;
- restores an older scene version;
- accepts an AI rewrite that changes an event;
- changes Story Bible/Canon while downstream scenes already exist.

V1 must make this divergence explicit rather than silently generating from stale truth.

## 2. Consistency state

Story fields:

```text
consistencyStatus: CLEAN | DIRTY | RECONCILING | NEEDS_REVIEW
dirtyFromSceneId: SceneId | null
```

If several edits occur, `dirtyFromSceneId` is the earliest affected committed scene.

## 3. Dirty marking

A committed scene document change does not need semantic analysis on every keystroke. After a deliberate save/checkpoint/AI action that may alter story meaning, the scene is marked potentially story-changing.

Conservative V1 rule:
- edits to an already committed scene with downstream generated content can mark the story dirty;
- purely pre-generation drafts do not require reconciliation;
- simple formatting changes may be classified safe by deterministic editor operations.

## 4. Generation guard

Before generating a downstream scene:

```text
if consistencyStatus != CLEAN:
    do not silently continue
```

The user/system must reconcile first or explicitly discard the prose/state change through a supported action.

## 5. Reconcile workflow

```text
Dirty Scene
  ↓
Capture immutable SceneVersion + document revision
  ↓
State Extractor reads edited scene and prior valid state
  ↓
ProposedStoryDelta
  ↓
Domain/Canon validation
  ↓
If valid: rebuild state from dirty boundary through already accepted downstream scenes using stored scene documents/deltas or bounded re-extraction
  ↓
CLEAN
```

If reconciliation encounters ambiguous/contradictory downstream content, set `NEEDS_REVIEW` and surface affected scene range.

## 6. Alpha limitation

Alpha does **not** build a full dependency graph that automatically repairs only affected downstream scenes.

It can use a conservative policy:

- reconcile state sequentially from the dirty boundary;
- mark downstream text as potentially stale;
- offer “Regenerate from here” or “Keep text and reconcile sequentially.”

V1.5 introduces precise impact analysis and targeted downstream repair.

## 7. Canon changes

When a locked/authoritative Story Bible fact changes manually:
- increment Canon/domain version;
- mark affected generated story consistency for review if the fact predates generated scenes;
- active generation detects stale version before commit.

## 8. Version restoration

Restoring an older SceneVersion creates a new current version; it does not mutate the historical version. If the restored content may alter story truth, apply the same dirty/reconciliation rules.

## 9. UX

Story Studio must show a clear status such as:

`Story changed from Scene 6 — reconcile before continuing generation.`

Primary actions:
- Reconcile;
- Regenerate from here;
- Review conflict when reconciliation cannot be resolved safely.

## 10. Tests

Required deterministic integration test:
1. Generate scenes 1–5.
2. Modify Scene 2 from “Lan survives” to “Lan dies.”
3. Verify dirty boundary = Scene 2.
4. Attempt Scene 6 generation and verify it cannot use stale clean state.
5. Reconcile and verify current StoryState reflects Lan's death.
6. Continue generation and verify committed output cannot claim Lan is alive unless the narrative explicitly changes that state validly.
