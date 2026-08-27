# ADR-0017: Structured editor

## Context

Story Studio needs custom structured blocks, stable block IDs, controlled
serialization, ordered patches, and no forced CRDT dependency in Alpha.

## Decision

Use TipTap/ProseMirror behind the `StoryEditor` adapter. Persist the canonical
scene document as a versioned JSONB-shaped structure with stable block IDs; the
editor framework is not allowed to become the domain model.

## Consequences

TipTap provides a mature transaction and schema boundary while preserving a
future replaceable editor seam. The first implementation must keep patching and
serialization in an adapter so Alpha does not couple API contracts to editor
internals.

## Revisit trigger

Revisit if stable-ID patching, accessibility, or bundle/runtime cost cannot meet
the Story Studio acceptance tests.

