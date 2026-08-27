# Knowledge / RAG / Research Architecture V2

## 1. Knowledge categories

- **Story Canon/State** — authoritative product/domain truth; not a vector-store document.
- **Lore** — user-authored world reference.
- **Research** — factual/reference material supplied by the user in Alpha; public Web Research later.
- **Style Reference** — future style-analysis input, not fact authority.

## 2. Alpha ingestion

Core Alpha may accept:
- pasted text;
- TXT;
- Markdown.

PDF/DOCX enter Beta after parser/security/fidelity tests. Source files use ObjectStorage where needed; metadata/chunks live in PostgreSQL.

## 3. Chunking/index

Baseline:
- section/paragraph-aware chunks;
- source/project metadata;
- PostgreSQL full-text;
- pgvector embedding;
- exact vector search first unless scale benchmarks justify ANN.

## 4. Retrieval

```text
project/workspace scope filter
→ FTS candidates + vector candidates
→ simple merge/RRF
→ top-K evidence
```

Add LLM query understanding, reranking and compression only after eval evidence.

## 5. Provenance

Retrieved evidence records source/chunk identity and section/position where available. Generation context stores evidence IDs.

## 6. Authority

`Locked/authoritative Story truth > Story rules/Lore authority > Research evidence > general reference.`

Research/Lore never silently promote themselves into Canon.

## 7. Prompt-injection boundary

Retrieved/uploaded content is untrusted data. Context assembly clearly delimits it as evidence and prevents it from changing system instructions, tools, routing, user locks or Canon authority.

## 8. Web Research

Public search/fetch/research-agent behavior is **V1.3**. It requires dedicated source, fetch, trust, security and provenance policies rather than being hidden inside Alpha RAG.

## 9. VectorStore abstraction

Application code depends on `VectorStore`. V1 implementation is PostgreSQL + pgvector. A dedicated vector database is a later scaling decision.
