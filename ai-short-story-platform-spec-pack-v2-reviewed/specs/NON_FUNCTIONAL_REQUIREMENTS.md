# Non-Functional Requirements — V2

## Reliability

- A committed scene cannot be lost because later AI/provider work fails.
- Generation is resumable at durable boundaries.
- Retried side effects are idempotent.
- PostgreSQL product state is recoverable independently of Temporal history.
- Large AI artifacts are stored outside Temporal workflow history and referenced by stable IDs/hashes.

## Consistency

- Locked story truth cannot be automatically overwritten by AI.
- Domain writes validate expected story/canon/document versions.
- Manual prose changes can mark the story dirty and block silent downstream generation.
- Restore operations respect the same consistency rules as manual edits.
- There is one authoritative write path per fact; projections cannot become competing writable truths.

## Performance targets for Alpha

Initial release targets, measured in staging and revised from observed data:

- non-AI API p95 < 500 ms under expected Alpha load;
- document autosave acknowledgement p95 < 750 ms under expected Alpha load;
- Story Studio editor typing has no server round-trip dependency;
- initial story/generation request returns an ID rather than holding a long HTTP request;
- first visible completed scene target <= 120 seconds in the Standard path for the selected provider/model and typical scene size;
- generation progress remains observable through reconnectable REST + SSE.

These are product SLO targets, not guarantees for external-model latency spikes.

## Cost envelope

Before Alpha release, define a maximum allowed model cost per 10k generated words for Standard mode. All V0/V1 eval reports must record actual cost and latency. A model/prompt change that exceeds the release budget requires an explicit quality/economic approval.

## Security

- Every resource access is workspace-authorized.
- Cross-workspace retrieval leakage must be impossible under tested query paths.
- Provider secrets never reach the browser.
- Python workers have no unrestricted domain-write path.
- Object access uses controlled/presigned URLs where relevant.
- User/reference documents are **untrusted data**, not instructions. Retrieved text cannot override system rules, tool permissions, Canon authority or user locks.
- Uploaded file processing validates MIME/type/size and runs in constrained parsers/processes appropriate to the selected deployment.

## Privacy

- Production logs do not store raw unpublished story text, prompts or full ContextBundles by default.
- Trace records use IDs, hashes, versions, token counts, timing and error classes unless content logging is explicitly enabled under a documented retention policy.
- Workspace knowledge is isolated.
- Purge removes DB data, vectors and object artifacts subject to legal/backup retention policy.

## Backup and disaster recovery

Before production launch define and test:

- PostgreSQL backup cadence and point-in-time recovery strategy;
- object-storage backup/replication policy;
- Temporal persistence backup per selected deployment;
- target RPO and RTO;
- a documented restore drill with evidence that story/project data can be recovered.

Alpha staging must complete at least one restore drill before public launch.

## Observability

Trace chain:

`Request → GenerationRun → Workflow/Run → Activity → Capability → Model/Prompt → ContextSnapshot/Artifact IDs → Usage/Cost → Result/Error`

Track at minimum:
- workflow success/failure/retry;
- scene generation latency;
- provider errors/rate limits;
- context size;
- token/cost;
- structured-output repair rate;
- state-extraction quality;
- dirty/reconciliation frequency and failures;
- autosave conflicts;
- retrieval scope failures.

## Maintainability

- Cross-runtime contracts are versioned.
- Domain code does not depend on ORM/provider/Temporal SDK details.
- Workflow code stays deterministic; external I/O occurs in activities.
- Prompt, model and workflow versions are traceable.
- Software tests and AI evals remain separate.

## Accessibility

Interactive Story Studio controls are keyboard reachable, have visible focus and use textual/icon status in addition to color.
