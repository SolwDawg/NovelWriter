# AI Capability & Model Router V2

## 1. Principle

Story/application code requests capabilities, not provider-specific model APIs.

```text
Capability Request
→ Routing Policy
→ Provider Adapter
→ Structured Result
```

## 2. Alpha capabilities

- intent interpreter;
- story architect/planner;
- scene writer;
- state extractor;
- scene critic;
- story critic;
- summarizer;
- embedding if knowledge is enabled.

Style Analyzer, research synthesizer and advanced reranker are later capabilities.

## 3. Capability contracts

Every cross-runtime request/result has a versioned schema and validation. Structured output is preferred where the task is structured.

## 4. V1 routing policy

V1 uses static configuration, for example:

```yaml
scene_writer:
  provider: primary
  model: writer-model
state_extractor:
  provider: primary
  model: structured-model
```

The Router still enforces capability/provider abstraction and may use one fallback provider/model for transient availability.

Do not implement dynamic historical scoring, self-optimizing routing or an admin control plane until usage/eval data exists.

## 5. Provider adapter

Adapters normalize:
- text generation;
- structured generation;
- embeddings if supported;
- streaming where used;
- token/usage/latency/error metadata.

## 6. Budget

Every GenerationRun records estimated/actual usage. V1 enforces a simple per-run/per-capability budget policy. Advanced reservation/optimization can evolve later.

## 7. Error policy

Distinguish:
- transient provider/network/rate-limit;
- context/model incompatibility;
- invalid structured output;
- domain/canon conflict;
- budget failure.

Do not blind-retry semantic/domain conflicts.

## 8. Local LLM

Keep `LocalProvider` as a future adapter. No local-serving stack is required in V1.
