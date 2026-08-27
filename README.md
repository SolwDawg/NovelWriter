# NovelWriter

Monorepo foundation for the AI short-story platform described in
`ai-short-story-platform-spec-pack-v2-reviewed`.

## Current slice

- Canonical cross-runtime contracts under `packages/contracts`.
- TypeScript and Python equivalents for the first eight contracts.
- Health/startup-only process shells for web, API and workflow worker.
- Python AI-worker shell that can be extended with the proven V0 engine.
- PostgreSQL/pgvector and Temporal development services in
  `infra/docker/compose.yml`.
- The live-provider benchmark and human paired evaluation are intentionally
  deferred; the harness remains under
  `ai-short-story-platform-spec-pack-v2-reviewed/experiments/story-engine-v0`.

## Local verification

```powershell
pnpm install
pnpm lint
pnpm test
pnpm typecheck
pnpm test:python
```

The Python worker has no runtime dependency yet. If `uv` is available, the
equivalent project command is:

```powershell
uv run pytest services/ai-worker/tests -q
```

Start the infrastructure when needed by the next vertical slice:

```powershell
docker compose -f infra/docker/compose.yml up -d postgres temporal
```

Run the process shells in separate terminals:

```powershell
pnpm dev:api
pnpm dev:web
pnpm dev:workflow-worker

$env:PYTHONPATH = "services/ai-worker/src;packages/contracts/python"
python -m story_platform_ai.main
```

For live V0 evaluation, create a local `env.txt` at the repository root with
two provider keys and a model line. The file is ignored and must never be
committed:

```text
your-first-openrouter-key
your-second-openrouter-key
model: minimax/minimax-m3:free
```
