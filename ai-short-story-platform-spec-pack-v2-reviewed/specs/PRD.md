# Product Requirements Document — V2 Reviewed

## 1. Product

Working name: **AI Short Story Platform**.

A browser-based AI Story Studio for creating and editing narration-ready fiction. The creator flow is simple by default; advanced story controls are available without turning the product into a chatbox or a prompt-engineering tool.

## 2. Core problem

Generic LLM long-form fiction workflows commonly suffer from:

- one-pass or poorly planned generation;
- forgotten character facts and inconsistent timeline/knowledge;
- weak scene-level control;
- unpredictable targeted rewrites;
- no durable recovery for long generation jobs;
- no reliable connection between manual prose edits and story state;
- style/reference/research/canon being mixed together;
- poor reproducibility of model context and generation decisions.

## 3. Product promise

A creator can enter a one-line idea, generate a coherent multi-scene story, edit or regenerate individual scenes, keep important story facts controlled, recover from workflow failures and export narration-ready text.

V1 Alpha officially targets **3,000–15,000 words**. The architecture supports 30,000 words; 15,000–30,000 becomes a Beta quality gate rather than an Alpha promise.

## 4. Primary personas

### Creator — primary
Needs fast setup, strong narrative hooks, clear spoken prose, reliable progress, simple AI editing and export.

### Writer — secondary
Needs outline control, canon locking, scene goals, versions, style rules and consistency diagnostics. Deeper story intelligence is staged after Alpha.

## 5. V1 Alpha journey

1. Sign in and enter personal workspace.
2. Create project/story.
3. Enter a one-line idea.
4. Optionally choose genre, target length, style preset/custom rules and outline review.
5. Start Standard generation.
6. Watch scene-level progress in Story Studio.
7. Edit completed scenes while downstream generation remains durability-safe.
8. Use contextual AI actions for local revisions.
9. Lock important canon facts.
10. Resolve dirty/reconciliation status when a story-critical manual edit changes prior truth.
11. Compare/restore scene versions.
12. Apply final TTS polish and export TXT/Markdown/DOCX.

## 6. V1 Alpha functional requirements

### Story creation
- One-line idea.
- Advanced settings override AI inference.
- Official target length 3k–15k.
- One officially optimized language selected before V0 evaluation.
- 2–3 optimized genres selected before V0 evaluation.
- One user-visible quality mode: `Standard`.

### Planning
- `StoryIntent`, `Premise`, `StoryBlueprint`.
- Chapter and scene planning.
- Optional outline review/approval.
- ScenePlan required core fields remain intentionally small.

### Generation
- Scene-by-scene durable generation.
- Context is assembled per scene.
- State extraction and deterministic validation before domain commit.
- State Extractor is the only AI component that proposes StoryDelta.
- Pause/resume/cancel at safe boundaries.
- Typed retry/failure behavior.
- Large AI artifacts referenced by ID rather than carried in workflow history.

### Story consistency
- Story has `CLEAN`, `DIRTY`, `RECONCILING` or `NEEDS_REVIEW` consistency status.
- Manual edits/restores that may alter story truth mark a dirty boundary.
- Downstream AI generation cannot silently continue from known-dirty state.
- Reconciliation extracts/validates state from the edited scene and rebuilds the current projection from the dirty boundary.
- Automatic dependency-specific downstream repair is not Alpha scope.

### Story Studio
- Three-panel desktop workspace.
- Chapter/Scene navigator.
- Structured scene document editor with stable block IDs.
- Local editing plus batched optimistic autosave.
- SSE generation progress.
- Basic Bible/Outline/Style/Versions panels.
- Clear dirty/consistency state UX.

### V1 Alpha AI actions
- Rewrite.
- Expand.
- Shorten.
- Increase Tension.
- Improve Hook.
- TTS Polish.
- Regenerate Scene.

Writer-level actions such as Change POV, Foreshadowing and structural pacing changes may be added after the stable core editing loop.

### Story Bible
Alpha supports:
- Characters.
- Relationships.
- Locations where useful.
- World Rules.
- Canon Facts.
- Open Story Threads.
- Lock/unlock authoritative facts.

### Versioning
- Autosave document revision.
- Immutable scene versions for deliberate AI/manual checkpoints.
- Compare and restore.
- Restore marks story dirty if the restored content can alter committed state.
- First Draft and Final story snapshots.

### Style
- Built-in preset(s).
- Custom scoped rules.
- Reusable Style Profile.
- Reference-derived Style Analyzer is deferred to V1.2.

### Knowledge
Alpha core supports pasted text/TXT/Markdown project knowledge. Retrieval is project-scoped and provenance-aware. PDF/DOCX ingestion can enter Beta after parsing and security tests pass.

### Export
- TXT.
- Markdown.
- DOCX.

## 7. Explicitly out of V1 Alpha

- Web Research.
- Reference-based style analysis.
- 30k-word official quality promise.
- Multiple user-visible quality tiers.
- Automatic scene dependency graph and downstream targeted repair.
- Specialized multi-agent critic suite.
- Adaptive/historical Model Router control plane.
- Audio generation.
- CRDT/realtime co-editing.
- Team collaboration UI.
- Local LLM serving.
- Qdrant, Kubernetes or microservice extraction.

## 8. Alpha product success criteria

The product is ready to advance to Beta only when:

- the V0 structured engine shows a material quality advantage over the selected simpler baseline or an explicitly accepted cost/quality trade-off;
- a 10k-class story can complete, pause/resume and recover from a simulated provider failure without duplicate/lost committed scenes;
- locked-canon deterministic tests pass 100%;
- cross-workspace knowledge leakage tests pass 100%;
- manual-edit dirty/reconciliation flow is proven end-to-end;
- structured AI outputs and state extraction meet the thresholds in `ACCEPTANCE_AND_EVALS.md`;
- production-like cost per 10k words remains inside the configured release budget.
