# Versions Roadmap V2

## V0 — Engine Proof

Goal: prove hierarchical generation/state reconciliation is worth the complexity.

Deliverables:
- Python evaluation harness;
- baselines A/B/C/D;
- 30+ story prompts;
- structured state/canon/thread engine;
- cost/latency/human comparison.

Exit: pass V0 gates in `specs/V0_ENGINE_PROOF.md`.

## V1 Alpha — Reliable Creator Core

Goal: one end-to-end creator product that can generate/edit/recover a coherent 3k–15k story.

Includes:
- auth/personal workspace;
- wizard;
- durable generation;
- Story Studio;
- StoryState/Canon/Threads;
- manual-edit reconciliation;
- simple Style Profile;
- basic versions;
- Standard quality mode;
- export;
- optional minimal user-supplied knowledge.

## V1 Beta — Broaden Proven Core

- official 15k–30k after evals;
- second language;
- more genre coverage;
- PDF/DOCX knowledge;
- stronger RAG if needed;
- Fast/High Quality if measured value exists;
- improved story-level diagnostics.

## V1.2 — Creator Productivity

- reference-derived Style Profiles;
- richer reusable presets;
- project/story duplication/templates;
- batch/advanced editing actions;
- better creator export/workflow ergonomics.

## V1.3 — Research & Knowledge

- Web Research toggle;
- research questions/planning;
- search/fetch/source provenance;
- source trust/contradiction handling;
- JIT research where justified;
- workspace reusable knowledge library.

## V1.5 — Story Intelligence

- scene/fact/thread dependency graph;
- structural impact analysis;
- precise downstream revalidation;
- automatic targeted downstream repair;
- character-arc diagnostics;
- tension/pacing curves;
- plot-hole/unresolved-thread intelligence.

## V2 — Multi-output Story Platform

- prose-first renderer/UX;
- multiple language editions from one story model;
- output-mode conversion grounded in shared StoryState/Blueprint;
- screenplay renderer may begin as experimental.

## V2.x — Audio Creator Suite

- TTS provider integration;
- speaker/voice mapping;
- pronunciation dictionary;
- block/scene audio segments;
- partial regenerate/cache;
- MP3/WAV export.

## V3 — Professional Writer Studio

- branches/alternate story lines;
- advanced timeline/relationship/world tools;
- deeper revision planning;
- story diagnostics dashboard;
- what-if/alternative outline workflows.

## V3.x — Collaboration

- team workspaces;
- editor/viewer roles;
- comments/suggestions;
- realtime CRDT collaboration;
- editorial approval flows.

## V4 — Local/Private AI

- local embeddings/rerank/extractor/summarizer first;
- local planner/writer when evals justify;
- Cloud/Hybrid/Local-only routing modes;
- GPU worker pools.

## V4.x — Scale Infrastructure

Only when traffic/ops demand:
- dedicated vector DB;
- selective service extraction;
- Kubernetes or equivalent orchestration.

## V5 — Platform/Ecosystem

- public API/webhooks;
- plugin/skill framework;
- organizational templates/evaluators;
- creator integrations and automation.
