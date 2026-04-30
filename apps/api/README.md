# @flo101/api

FastAPI service implementing the Critic agent.

## Layout

```
src/flo101_api/
├── domain/          # pure types, zero I/O
├── llm/             # OpenRouter gateway + prompt registry
├── synthesizer/     # SkillSpec generator
├── critic/          # LangGraph StateGraph + nodes
├── corpus/          # ingest, embed, retrieve (sqlite-vec)
├── sandbox/         # subprocess + ulimits
├── api/             # FastAPI routes
├── db/              # SQLite repositories
├── observability/   # structlog + LangSmith hooks
├── scripts/         # one-off scripts (export_schema, seed)
├── config.py        # pydantic-settings
└── main.py          # FastAPI app factory
```

See top-level `ARCHITECTURE.md` for design.
