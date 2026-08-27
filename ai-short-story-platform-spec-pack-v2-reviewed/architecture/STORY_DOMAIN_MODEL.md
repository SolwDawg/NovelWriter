# Story Domain Model V2

## 1. Aggregate hierarchy

```text
Workspace
└── Project
    └── Story
        ├── Premise / Blueprint
        ├── Chapters
        │   └── Scenes
        │       └── SceneDocument
        ├── Story Bible
        ├── Current StoryState
        ├── StateDelta history
        ├── SceneVersions
        └── StorySnapshots
```

`Project` remains a product container; `Story` is the narrative aggregate.

## 2. Story

Core fields:
- id/projectId/title/status;
- targetWordCount;
- languageProfileId/styleProfileId/genreProfileId;
- outputMode;
- currentStateVersion/currentStateId;
- canonVersion;
- consistencyStatus;
- dirtyFromSceneId nullable;
- createdAt/updatedAt.

## 3. Premise and Blueprint

Premise normalizes the user's raw idea. Blueprint defines macro narrative structure, protagonist arc, conflict, reversals, climax, resolution and target distribution.

They are planning truth, not generated prose.

## 4. Chapter and Scene

Chapter groups scenes and pacing.

Scene is the primary generation/revision unit.

### Minimal required ScenePlan
- purpose/narrative function;
- POV, location and participants where relevant;
- required outcome;
- required facts/context;
- forbidden reveals;
- active threads;
- target tension;
- target word count.

Optional richer planning data lives in versioned JSON metadata rather than becoming mandatory columns/contracts.

## 5. First-class story entities

V1 may include:
- Character;
- CharacterRelationship;
- Location;
- WorldRule;
- StoryThread;
- CanonFact for assertions that are not already authoritatively owned by a first-class entity.

## 6. One-authority rule

A narrative truth must have one authoritative write owner.

Example: if `CharacterRelationship` owns “Nam is Minh's brother,” do not maintain an independently writable CanonFact expressing the same relationship. If a search/index projection exists, it is derived from the relationship.

This prevents data divergence between Story Bible objects and generic facts.

## 7. CanonFact

Use for explicit assertions requiring authority/lock/provenance where no richer domain entity is the canonical owner.

Fields/concepts:
- subject reference;
- predicate;
- value/object;
- validity/lifecycle;
- introduced scene;
- source/provenance;
- locked flag.

## 8. StoryState

V1 uses StoryState as the materialized current narrative projection rather than requiring a separately normalized CharacterState table for every state dimension.

Typical shape:

```json
{
  "schemaVersion": 1,
  "characters": {
    "char_nam": {
      "locationId": "loc_house",
      "emotion": "afraid",
      "knowledgeFactIds": ["fact_x"],
      "inventory": ["obj_watch"]
    }
  },
  "openThreadIds": ["thread_missing_brother"],
  "timeline": {"storyClock": "..."}
}
```

Historical change is stored as `StoryStateDelta`. More specialized projections such as CharacterState tables may be introduced when query/eval needs justify them.

## 9. StoryStateDelta

Only the State Extractor proposes a delta after reading an accepted candidate scene document. Domain validation then accepts/rejects/repairs the proposal.

Delta categories may include:
- character state;
- knowledge gained/lost;
- inventory/object ownership;
- location/time;
- thread progression;
- authoritative fact changes allowed by domain rules.

## 10. StoryThread

Tracks unresolved narrative promises/questions with status `OPEN`, `ADVANCING`, `RESOLVED` or `DROPPED`.

## 11. SceneDocument

Structured document with stable block IDs. V1 may persist the whole scene document as versioned JSONB because scenes are relatively small.

Example:

```json
{
  "schemaVersion": 1,
  "blocks": [
    {"id":"blk_1","type":"narration","text":"..."},
    {"id":"blk_2","type":"dialogue","speakerId":"char_nam","text":"..."}
  ]
}
```

Stable IDs still support targeted patches, diffs and future TTS mapping.

## 12. Versioning

A SceneVersion is immutable and can snapshot:
- document JSON;
- scene-plan version/reference;
- source: manual/AI/regenerate/restore;
- generation/context metadata IDs.

Diff is computed on demand in V1.

## 13. Consistency status

```text
CLEAN
DIRTY
RECONCILING
NEEDS_REVIEW
```

`dirtyFromSceneId` identifies the earliest committed scene whose prose/model may no longer match the current StoryState history.

See `STORY_CONSISTENCY_RECONCILIATION.md`.

## 14. Domain invariant

**Generated or edited prose never becomes authoritative story truth merely because it exists in a document. It becomes truth only after validated reconciliation/commit.**
