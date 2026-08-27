# ADR-0022: Defer the V0 live and human benchmark gate during foundation work

- Status: Accepted for development sequencing
- Date: 2026-08-27

## Context

The live-provider benchmark and human paired evaluation are required evidence
for the official V0 release gate. The harness and offline fixture benchmark are
available, but the free live route is rate-limited on the structured multi-call
path and the human sample has not been completed.

## Decision

Allow implementation of the monorepo foundation and early product/domain
vertical slices before completing the live and human V0 gate, by explicit
product decision. Keep the V0 gate marked `NOT READY`; do not describe the
Alpha as release-ready until the benchmark evidence is complete.

The existing resumable harness remains the source of truth for returning to the
benchmark later. Generated story output and provider credentials stay local.

## Consequences

- Task 2 and subsequent development work may proceed without claiming V0 proof.
- Release/Alpha work must still include live-provider measurements and human
  paired evaluation before launch.
- Any architecture change caused by benchmark findings must be applied before
  the corresponding production slice is considered stable.
