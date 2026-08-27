# Monorepo Architecture V2

## 1. Repository

```text
story-platform/
├── apps/
│   ├── web/                 # Next.js
│   ├── api/                 # NestJS HTTP/SSE
│   └── workflow-worker/     # TypeScript Temporal worker
├── services/
│   └── ai-worker/           # Python Temporal AI worker
├── packages/
│   ├── contracts/
│   ├── domain-types/
│   ├── config/
│   ├── observability/
│   └── test-fixtures/
├── infra/
├── evals/
├── docs/
└── scripts/
```

V0 engine proof may initially live under `services/ai-worker/evals/v0/` or a focused `experiments/story-engine-v0/` package, but successful contracts/fixtures graduate into the production packages.

## 2. `apps/api`

NestJS modular monolith with domain/application/infrastructure/presentation boundaries.

## 3. `apps/workflow-worker`

Contains Temporal workflow definitions and domain-side activity registration. It imports approved shared application/domain packages rather than duplicating business logic. It has a separate process entrypoint/container from the API.

## 4. Python worker

Organize by capability, not vague “agents”:

```text
capabilities/
  intent/
  planning/
  scene_writer/
  state_extractor/
  critics/
  summarizer/
  embeddings/
model_router/
providers/
context/
temporal/
schemas/
```

## 5. Cross-runtime contracts

Canonical versioned JSON Schema/OpenAPI-compatible schemas in `packages/contracts`, generating TypeScript and Python/Pydantic types where practical.

## 6. Prompts

Versioned prompt templates live with the AI worker/capability. Prompt version is traced in every important AI execution.

## 7. Infrastructure services

Development Compose profile includes at most what the active slice needs. Full Alpha can include:
- PostgreSQL + pgvector;
- Redis;
- Temporal + UI;
- selected S3-compatible object storage if artifact/upload paths need it;
- web/api/workflow-worker/ai-worker.

BullMQ is not a required V1 service.

## 8. Tests/evals

- deterministic unit/integration/E2E tests near services/apps;
- AI evaluation fixtures and harness under `evals/`;
- V0 baselines preserved for regression comparisons.
