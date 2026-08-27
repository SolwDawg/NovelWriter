# ADR-0020: Alpha object storage

## Context

Large AI artifacts, uploads, and exports must not be carried through Temporal
history. Application code must depend on an S3-compatible `ObjectStorage`
interface rather than a vendor SDK.

## Decision

Use MinIO for local development and early self-hosted deployments through an
S3-compatible adapter. Keep the interface compatible with a managed S3 provider
for later deployment changes.

## Consequences

Developers can exercise claim-check/artifact flows locally without changing
application code. Deployment still needs bucket lifecycle, encryption, access
policy, and backup configuration before production.

## Revisit trigger

Revisit when the deployment target, retention requirements, or operational data
durability needs make managed object storage preferable.

