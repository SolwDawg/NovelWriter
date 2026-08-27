# Temporal Workflow & Event Architecture V2

## 1. Temporal role

Temporal orchestrates long-running processes; PostgreSQL remains product truth.

Workflow state is deliberately small: IDs, versions, stage, progress and artifact references.

## 2. Processes

- `api` — NestJS HTTP/SSE process.
- `workflow-worker` — TypeScript Temporal workflows/domain-side activities.
- `ai-worker` — Python Temporal AI activities.

They may share contracts/packages but are separately deployable.

## 3. Alpha workflows

- `GenerateStoryWorkflow`.
- `ReconcileStoryWorkflow`.
- `RegenerateSceneWorkflow` / durable rewrite where needed.
- `ExportStoryWorkflow` only if export requires asynchronous artifact work.
- Knowledge ingestion workflow if Alpha knowledge is enabled.

Web Research/Style Analyze workflows are later.

## 4. GenerateStoryWorkflow

```text
initialize run
→ plan story
→ optional outline approval wait
→ for each scene:
    ensure story consistency CLEAN
    create context artifact
    generate scene artifact
    extract delta artifact/result
    validate/domain commit
    update progress
→ story critic/final revision
→ TTS polish
→ snapshot
→ complete
```

## 5. Claim-check/artifact pattern

Activities that produce large content write it to an artifact store and return:

```json
{
  "artifactId": "art_x",
  "contentHash": "...",
  "schemaVersion": 1,
  "usage": {}
}
```

Workflow history does not carry 10k–30k story text or giant context blobs.

## 6. Pause/resume/cancel

- Pause is observed at safe boundaries; current atomic/domain activity may finish.
- Resume continues from current committed state.
- Cancel preserves valid committed scenes and marks run cancelled.

## 7. Reconciliation

If story consistency is dirty, generation branches to `ReconcileStoryWorkflow` or pauses with a product-level needs-attention state. Do not continue with known-stale state.

## 8. Retry/error taxonomy

Retry transient infrastructure/provider failures with bounded backoff. Semantic/domain errors route to repair/reconcile branches rather than blind retry.

Typed categories include transient provider, rate limit, invalid AI output, stale context, canon conflict, dirty story, budget exceeded and unrecoverable domain error.

## 9. Idempotency

All side-effect activities use stable idempotency keys. Replayed/retried commit activities return existing results instead of duplicating versions/usage charges.

## 10. Progress

NestJS persists product-level `GenerationRun` status/progress. Browser reads REST state and SSE events; it never queries Temporal directly.

## 11. Workflow evolution

Keep workflow code deterministic and version changes replay-compatible. External I/O, model calls and DB access belong in activities.
