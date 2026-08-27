# System Architecture V2

## 1. Runtime topology

```text
Browser
  │
  ▼
Next.js
  │ REST / SSE
  ▼
NestJS API  ─────────────── PostgreSQL + pgvector
  │                         Redis
  │                         ObjectStorage (S3-compatible)
  │
  └── starts/controls Temporal workflows

Temporal Cluster
  │
  ├── TypeScript Workflow Worker (separate process)
  │      └── domain/application activities through NestJS-shared application services or dedicated activity adapters
  │
  └── Python AI Worker
         ├── capability runtime
         ├── model/provider adapters
         └── AI artifact read/write
```

The API and TypeScript workflow worker may share packages/code but are separately runnable/deployable processes.

## 2. Responsibility boundaries

### Next.js
Presentation, routing, Story Studio local/editor state, API calls and SSE. No direct database/Temporal/provider access.

### NestJS API/application/domain
Authoritative product commands/queries, auth/permissions, Story/Canon/Document/Version/Knowledge/Usage state and workflow gateway.

### TypeScript workflow worker
Deterministic Temporal workflow definitions and domain-side activities. It does not become a second source of business truth.

### Python AI worker
Planning, generation, extraction, criticism, summarization, embeddings/retrieval helpers. It returns structured proposals/artifacts; it does not directly commit domain truth.

### PostgreSQL
Authoritative product state plus pgvector data for V1 retrieval.

### Temporal
Durable process state: what should happen next, retry/signal/timer history. Not canonical story content.

### Redis
Cache, rate limiting, ephemeral locks if needed and realtime fanout. V1 does not require BullMQ.

### ObjectStorage
Large uploads, exports and large AI artifacts. Application depends on `ObjectStorage`, not a specific vendor.

## 3. Large-payload rule

Temporal workflow/activity inputs and outputs should remain small. Large ContextBundles, raw source text, generated scene prose or document snapshots are stored as artifacts and referenced by:

```text
artifactId
contentHash
schemaVersion
owner/project scope
```

This limits workflow history growth and keeps content retention/policy under product control.

## 4. Deployment posture

Self-host-first, Docker Compose for development/early production. No Kubernetes requirement in V1. Scale API, workflow workers and Python AI workers independently when needed.

## 5. Key invariants

- `PostgreSQL = what is true in the product`.
- `Temporal = what process step runs next`.
- `Python = AI computation, not domain authority`.
- `RAG = evidence, not story truth`.
- `Prose = a representation that must reconcile with story state when edited`.
