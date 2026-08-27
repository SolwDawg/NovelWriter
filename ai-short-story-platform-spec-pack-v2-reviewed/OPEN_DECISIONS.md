# Explicitly Deferred Decisions — V2

These choices must be resolved before the first task that depends on them. They are not permission to change the architectural boundaries.

## 1. Primary V1 Alpha language

Choose exactly one officially optimized language for Alpha based on target customers and available human/eval capacity. The architecture remains multilingual. Other model-supported languages may be experimental but are not release-gated.

## 2. Initial V1 Alpha genres

Choose 2–3 optimized genres. Horror, Mystery and Thriller remain natural TTS-first candidates; select the final set using creator demand and evaluation coverage.

## 3. First cloud model/provider configuration

V1 needs one primary provider and may have one fallback provider. Select models with an explicit benchmark covering planning, prose quality, structured output, target-language quality, latency and cost.

## 4. Rich-text editor

Evaluate TipTap/ProseMirror and Lexical. Required properties: custom nodes/blocks, stable IDs, programmatic patches, controlled serialization and no forced CRDT dependency.

## 5. NestJS ORM/data layer

Evaluate Drizzle and Prisma, including migration control, PostgreSQL/pgvector ergonomics and repository-boundary fit. Domain/application code remains ORM-independent.

## 6. Authentication

Choose a self-hostable or application-owned session/auth solution. The invariant is `AuthenticatedPrincipal → WorkspaceMembership → Permission`.

## 7. S3-compatible object-storage implementation

Select an implementation/provider after current deployment, maintenance and licensing/distribution evaluation. Application code must depend only on `ObjectStorage`.

## 8. Reverse proxy

Nginx, Caddy or Traefik are acceptable if they support TLS, standard HTTP and long-lived SSE cleanly.

## 9. PDF/DOCX parser for Beta knowledge ingestion

Alpha does not require PDF/DOCX. Beta must select parsers based on extraction fidelity and operational footprint.

## 10. Commercial billing

Usage/cost accounting is required in V1. Checkout/subscription is not required until launch strategy demands it.
