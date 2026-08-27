# Product Interview & Reviewed Decisions V2

## Product intent

Build a website that uses AI to create short-to-novella-length fiction. The default user is a content creator who wants TTS-ready stories quickly; advanced controls support serious writers.

## Interview decisions retained

### Experience
- Hybrid onboarding: a one-line idea can generate immediately; advanced controls are optional.
- Adaptive planning: short stories can feel immediate, while longer stories always have explicit internal planning.
- Story Studio is hybrid: Chapter/Scene navigator, central editor, context/AI panel.
- AI actions are layered: a small creator set by default; advanced writer actions later.
- Story Bible is mostly automatic but inspectable/lockable.
- Style system supports presets and custom rules; reference-derived style is deferred from Alpha.
- Engine is general-purpose; only a narrow genre set is officially optimized per release.
- Architecture is multilingual; release optimization is deliberately narrower.

### Output
- TTS-first in V1, but Story Engine and data model remain output-neutral.
- V1 creates text, not audio.
- Stable scene/block identities prepare future TTS segment mapping.

### Story engine
- Hierarchical pipeline, not one-pass generation.
- Scene is the primary generation and revision unit.
- Canon/Story State are structured and separate from prose.
- Adaptive QA exists, but V1 implementation is intentionally small.
- Manual scene edits must reconcile back into Story State before downstream AI work.

### AI architecture
- Capability-based AI abstraction.
- NestJS owns business policy and authoritative writes.
- Python owns AI computation.
- Local LLM remains a future provider option.
- V1 routing is static/configured; adaptive routing is later.

### Knowledge
- Canon, Lore, Research and Style References remain separate concepts.
- User-provided knowledge can be retrieved through RAG.
- Web Research is not V1 Alpha; it moves to V1.3.

### Infrastructure
- Self-host-first posture.
- Next.js + NestJS + Python.
- PostgreSQL + pgvector.
- Temporal durable workflows.
- Redis for cache/rate-limit/realtime support.
- S3-compatible object-storage abstraction.
- Modular monolith + worker architecture.

### Collaboration
- V1 is single-user.
- Workspace/membership/permission and document sync boundaries remain collaboration-ready.

## Post-interview reviewed changes

The original interview often selected the broadest “D” option. V2 keeps those options as architectural direction but narrows what is implemented first.

### V0 is now mandatory

Before a full product implementation, prove that the structured engine materially beats simpler baselines on continuity and human preference at acceptable cost.

### V1 Alpha narrows the promise

- Official story length: 3,000–15,000 words.
- One primary optimized language.
- 2–3 optimized genres.
- One Standard quality mode.
- User-provided text knowledge only in the smallest Alpha path; PDF/DOCX can wait for Beta.
- No Web Research.
- No automatic downstream dependency repair.
- No reference-derived Style Analyzer.
- No adaptive model-routing UI.

### Story consistency becomes first-class

Manual prose editing, scene regeneration and version restoration can invalidate downstream story truth. V2 introduces `StoryConsistencyStatus` and `dirtyFromSceneId` with an explicit reconciliation workflow.

## Product success principle

The first proof of value is not feature count. It is whether a creator can repeatedly produce a coherent 10k-ish story, edit it, resume after failures and keep story facts under control with less effort than a generic chat workflow.
