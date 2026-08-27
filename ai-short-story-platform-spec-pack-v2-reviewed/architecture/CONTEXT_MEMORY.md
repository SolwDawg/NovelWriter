# Context & Memory Architecture V2

## 1. Principle

Build the smallest authoritative context needed for a capability; do not maximize token usage because a model supports a large window.

## 2. Memory hierarchy

### L0 hard authority
User locks, authoritative domain facts, world rules, required scene outcome.

### L1 current structured state
Current StoryState, relevant characters, thread status, timeline/location and secrets/knowledge.

### L2 local narrative memory
Recent scene text, recent scene summaries, current chapter summary.

### L3 long-term narrative retrieval
Relevant older scene summaries/excerpts selected by thread/callback/entity/semantic retrieval.

### L4 project knowledge
User-provided Lore/Research evidence scoped to the project.

### L5 writing profile
Style, genre, language and TTS rules.

## 3. Priority

`Hard authority > current state > narrative dependencies > local prose > project knowledge > style/reference preference`.

A knowledge source never overrides story canon/world rules unless the user explicitly promotes a fact through a domain action.

## 4. Summary levels

V1 requires Scene Summary and Chapter Summary. A Story Summary can be maintained for longer contexts. Arc summaries are optional until long-story evals show a need.

Structured state remains authoritative even when summaries are incomplete.

## 5. Retrieval

V1 narrative retrieval uses:
- exact entity/thread lookup;
- recency;
- optional semantic search over summaries/scene metadata.

Project knowledge baseline uses project scoping + PostgreSQL FTS + pgvector and a simple merge/RRF policy. LLM reranking/compression is added only if retrieval evals justify it.

## 6. Context budget

Each capability has a configured maximum context budget. When over budget:
1. remove low-relevance external knowledge;
2. shorten old excerpts/use summaries;
3. keep hard authority and current state.

## 7. Context snapshot/artifact

Record a small `GenerationContextSnapshot`:
- story/scene IDs;
- story/canon/state/document versions;
- selected entity/fact/thread IDs;
- selected scene/knowledge evidence IDs;
- writing profile version;
- prompt/model route version;
- `contextArtifactId` and content hash.

Raw ContextBundle content need not be stored in Temporal history.

## 8. Incremental update

After commit:
- apply StateDelta;
- create Scene Summary;
- update Chapter Summary when useful;
- update narrative retrieval index if enabled;
- emit committed event.
