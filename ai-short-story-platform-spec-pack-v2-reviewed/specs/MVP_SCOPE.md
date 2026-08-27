# V1 Alpha Scope

## In scope

### Product shell
- Authentication and personal workspace.
- Project/story lifecycle.
- Story setup wizard.

### Story Engine
- StoryIntent, Premise, StoryBlueprint.
- ChapterPlan and minimal ScenePlan.
- StoryState/current projection.
- StateDelta history.
- first-class Character/Relationship/WorldRule/StoryThread entities.
- CanonFact only where a first-class entity does not already own the truth, plus lock semantics.
- Scene-level generation/validation/commit loop.
- Manual-edit Story Consistency/Reconciliation.

### AI runtime
- Capability contracts: intent, architect/planner, scene writer, state extractor, scene critic, story critic, summarizer and embedding if Alpha knowledge is enabled.
- Provider abstraction.
- Static configured routing policy.
- One Standard user-visible quality mode.
- Usage/cost ledger.

### Workflow
- Temporal story-generation workflow.
- Scene regenerate/rewrite workflow where it requires durable AI work.
- Pause/resume/cancel.
- Typed retry behavior.
- Artifact-reference/claim-check pattern for large model inputs/outputs.

### Story Studio
- Three-panel layout.
- Scene navigator.
- Structured scene editor.
- Batched autosave and optimistic revision.
- SSE progress.
- Basic AI actions.
- Bible/Outline/Style/Versions panels.
- Dirty/reconciliation status and controls.

### Knowledge — minimal Alpha
- Pasted text, TXT, Markdown.
- Project scoping.
- PostgreSQL FTS + pgvector retrieval if knowledge is enabled for the chosen Alpha milestone.
- Provenance IDs.
- No Web Research.

### Versioning
- Document revision.
- Scene version snapshots.
- Compare/restore.
- First Draft / Final snapshots.

### Export
- TXT, Markdown, DOCX.

## Architecture-ready only

- collaboration-ready WorkspaceMembership/Permission model;
- replaceable document-sync boundary;
- S3-compatible `ObjectStorage`;
- `VectorStore` abstraction;
- future LocalProvider;
- future prose renderer;
- audio-ready stable IDs/metadata fields;
- prompt/model/workflow version tracking.

## Out of Alpha

- Web Research.
- PDF/DOCX knowledge ingestion unless promoted after early Alpha stability.
- style-reference analyzer.
- Fast/High Quality UI modes.
- dependency graph/impact analyzer/automatic downstream repair.
- specialized multi-pass critics.
- adaptive model routing/admin control plane.
- audio generation.
- CRDT/team collaboration.
- local LLM serving.
- dedicated vector DB.
- Kubernetes/microservices.

## Alpha release gate

1. Complete the V0 engine gate.
2. Generate a 10k-class story through Temporal with individual scene commits.
3. Pause/resume safely.
4. Simulate provider failure without duplicate/lost committed scenes.
5. Edit a committed scene, mark the story dirty, reconcile and continue generation from valid state.
6. Lock a canon fact and prevent automated overwrite.
7. Regenerate/restore a scene while preserving versions and consistency semantics.
8. Export the accepted story.
9. Meet security, privacy and eval thresholds.
