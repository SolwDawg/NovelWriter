# Codex Handoff — V2 Reviewed

## Required read order

1. `docs/superpowers/specs/2026-08-27-ai-short-story-platform-v2-design.md`
2. `specs/V0_ENGINE_PROOF.md` if the engine proof has not passed yet.
3. `specs/MVP_SCOPE.md`
4. `architecture/SYSTEM_ARCHITECTURE.md`
5. `architecture/STORY_CONSISTENCY_RECONCILIATION.md`
6. The subsystem spec for the task.
7. `docs/superpowers/plans/2026-08-27-ai-short-story-platform-v2-plan.md`
8. `OPEN_DECISIONS.md` before any task affected by an unresolved choice.

## Non-negotiable boundaries

- Do not collapse generation into one long prompt call.
- Do not let Python directly mutate Story Canon or other product truth.
- Do not treat RAG/vector retrieval as Story Canon or current Story State.
- Do not expose Temporal/database/provider details to the browser.
- Do not place large prose/context payloads in Temporal workflow state/history when an artifact reference can be passed.
- Keep the HTTP API process separate from the Temporal workflow-worker process.
- V1 Alpha does not include Web Research, CRDT, audio generation, local-LLM serving, Kubernetes, microservices, automatic dependency repair or an adaptive model-routing control plane.
- Cross-runtime payloads are versioned and schema validated.
- Deterministic rules use deterministic tests; creative quality uses evals and human rubrics.

## Scope discipline

If a requested implementation belongs to V1.2, V1.3, V1.5 or later, do not silently pull it into Alpha. Record the requested scope change before implementation.

## Delivery discipline

Implement vertical slices. Every slice must leave a runnable, testable system. Establish fake/deterministic AI providers before live-model workflow tests. Record architecture changes in ADRs.
