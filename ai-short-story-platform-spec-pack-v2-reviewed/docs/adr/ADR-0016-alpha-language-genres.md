# ADR-0016: Alpha language and genre set

## Context

The reviewed specs require exactly one officially optimized language and two or
three officially optimized genres before the V0 benchmark. The workspace owner
communicates in Vietnamese, and the product is TTS-first, so the first fixture
set should be native-language and continuity-heavy rather than translation-first.

## Decision

For the initial V0/Alpha benchmark baseline, lock:

- Language: `vi-VN` (Vietnamese).
- Genres: `Mystery`, `Thriller`, and `Horror`.

| Candidate | Evaluation coverage | TTS fit | Decision |
| --- | --- | --- | --- |
| Vietnamese | Available for the initial product owner and fixture authoring | Strong when written natively | **Selected** |
| English | Broadest model/eval ecosystem | Strong | Deferred as an experimental comparison |
| Vietnamese + English | Doubles the release matrix | Mixed | Rejected for Alpha scope |

The selected genres are deliberately narrow, share useful suspense/continuity
traps, and match the TTS-first product thesis.

## Consequences

The committed V0 cases use Vietnamese and cover the three selected genres. The
architecture remains multilingual, but another language is not release-gated by
this decision. Alpha quality claims must not be generalized to unsupported
languages or genres.

## Revisit trigger

Revisit this ADR if V0 human evaluation shows insufficient Vietnamese quality or
if user research identifies a different primary audience before Alpha release.

