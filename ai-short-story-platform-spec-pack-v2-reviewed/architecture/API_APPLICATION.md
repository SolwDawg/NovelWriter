# API & Application Architecture V2

## 1. Boundary

`Next.js → /api/v1 NestJS → application/domain → infrastructure`.

The browser never knows Temporal workflow names, database tables or model providers.

## 2. NestJS modules

Core Alpha modules:
- identity/workspace/project;
- story/story-bible;
- document/versioning;
- style/genre/language;
- generation/workflow-gateway;
- ai-routing/usage;
- knowledge if enabled;
- storage/realtime.

Research/admin-control-plane modules are later.

## 3. Command/query semantics

Commands mutate product state; queries read it. Controllers authenticate/validate/dispatch and do not contain workflow/provider logic.

## 4. Key APIs

```text
POST /api/v1/projects
POST /api/v1/projects/:projectId/stories
GET  /api/v1/stories/:storyId

POST /api/v1/stories/:storyId/generations
GET  /api/v1/generations/:id
POST /api/v1/generations/:id/pause
POST /api/v1/generations/:id/resume
POST /api/v1/generations/:id/cancel
GET  /api/v1/generations/:id/events   # SSE

GET  /api/v1/scenes/:sceneId
GET  /api/v1/documents/:documentId
POST /api/v1/documents/:documentId/changes

POST /api/v1/scenes/:sceneId/ai-actions
GET  /api/v1/scenes/:sceneId/versions
POST /api/v1/scenes/:sceneId/versions/:versionId/restore

GET/PATCH focused Story Bible resources
POST /api/v1/stories/:storyId/reconcile
```

## 5. Autosave

Document change request contains `baseRevision`, `clientMutationId` and ordered operations. Backend applies against current revision and returns a new revision or conflict.

## 6. Consistency API

Story response exposes:
- consistency status;
- dirtyFromSceneId;
- reconciliation issue summary when present.

Generation command rejects/pauses if a dirty story would produce downstream output without reconciliation.

## 7. AI actions

Use registered actions, not arbitrary `/ai` prompt endpoints. Freeform instructions may supplement a known action but cannot bypass Canon/domain constraints.

Whole-scene regeneration creates a candidate/version and preserves the previous accepted version.

## 8. Auth

Authorization is based on `AuthenticatedPrincipal → WorkspaceMembership → Permission`, not hard-coded `project.userId == user.id` assumptions.

## 9. DTO/domain separation

Public DTOs are not ORM/domain entities. Stable error codes and request IDs are part of the API contract.

## 10. SSE

SSE is notification, not authority. After disconnect/reconnect, frontend reloads authoritative generation state via REST and then resumes events.
