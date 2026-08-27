# ADR-0018: PostgreSQL data access

## Context

The domain requires PostgreSQL, JSONB snapshots, optimistic concurrency,
transactional outbox behavior, and a future pgvector integration. Domain code
must remain independent of the data-access library.

## Decision

Use Drizzle ORM and SQL migrations for the NestJS API. Repositories and a small
unit-of-work boundary own all Drizzle usage; domain/application services receive
interfaces rather than ORM records.

| Option | Fit | Main trade-off | Decision |
| --- | --- | --- | --- |
| Drizzle | SQL-first, explicit migrations, good JSONB/Postgres fit | More repository code | **Selected** |
| Prisma | Strong generated client and ecosystem | More opinionated migration/client boundary | Deferred |
| Handwritten SQL only | Maximum SQL control | Higher boilerplate and consistency risk | Rejected for Alpha |

## Consequences

PostgreSQL remains authoritative and JSONB can evolve without premature table
normalization. pgvector-specific queries stay in infrastructure adapters.

## Revisit trigger

Revisit if migrations, pgvector ergonomics, or repository testability become a
measured bottleneck.

