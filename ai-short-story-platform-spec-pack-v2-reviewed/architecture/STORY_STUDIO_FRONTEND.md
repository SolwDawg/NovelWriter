# Story Studio Frontend Architecture V2

## 1. Layout

Desktop default:

```text
Story Navigator | Scene Editor | Context Panel
```

Both side panels can collapse. Focus Mode can show only the editor.

## 2. Navigator

Shows Chapters/Scenes with lightweight status:
- planned;
- generating;
- complete;
- dirty/needs review;
- revised.

Alpha does not promise dependency-aware drag/drop repair. Structural reordering after generation may mark the story dirty and require reconciliation/regeneration.

## 3. Editor

Editor consumes a `StoryEditor` abstraction:
- load document;
- get selection;
- apply patch;
- get blocks;
- subscribe changes;
- focus/highlight block.

Concrete editor framework remains an open kickoff choice.

## 4. Stable blocks

Users see normal prose, not technical IDs. Stable block IDs power targeted AI patches, version comparison and future TTS mapping.

## 5. Autosave

Typing stays local. Changes are batched/debounced and serialized through a mutation queue using `baseRevision`. Status: Saved, Saving, Unsaved, Offline, Conflict.

## 6. Alpha AI actions

Default:
- Rewrite;
- Expand;
- Shorten;
- Increase Tension;
- Improve Hook;
- TTS Polish;
- Regenerate Scene.

Use inline proposal/accept/reject for local changes where practical. Whole-scene regeneration preserves old version.

## 7. Context panel

Alpha tabs:
- AI;
- Bible;
- Outline;
- Style;
- Versions;
- Knowledge only if enabled.

## 8. Story consistency UX

When a committed scene edit/restore invalidates structured state:

```text
Story changed from Scene 6.
Reconcile before continuing generation.
```

Actions:
- Reconcile;
- Regenerate from here;
- Review conflict.

Do not hide dirty state behind a generic warning icon.

## 9. Generation progress

Show scene-level progress without blocking the entire studio. Users can inspect completed scenes. Editing a completed upstream scene can trigger dirty status; the UI explains the consequence.

## 10. Frontend state

Separate:
- server query/cache state;
- editor local state/pending operations;
- ephemeral UI state;
- SSE-derived workflow view state.

Do not store the entire project/editor/workflow in one global mutable store.

## 11. Mobile

Alpha is desktop-first. Mobile may support reading/status/light edits but not full feature parity.
