# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DocuFlow-AI converts software requirement documents (PDF/DOCX) into structured design documents using LLM-powered analysis with LangGraph orchestration.

## Build & Run

**Backend (Python 3.11+, Windows):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .   # or: uv sync
```

**CLI:**
```powershell
docuflow all -p <project> -m gpt-5.2       # Full pipeline
docuflow init -p <project> -m gpt-5.2      # Phase 1: glossary + DAG
docuflow run -p <project>                   # Phase 2: module generation
docuflow overview -p <project>              # Phase 3: system/interface/DB design
docuflow assemble -p <project>              # Phase 4: assemble final document
docuflow status -p <project>                # Check progress
docuflow models                             # List available models
```

**API:** `docuflow-api` starts FastAPI on localhost:8000 (docs at /docs)

**Frontend:**
```powershell
cd docuflow/frontend && npm ci
npm run dev          # Dev server
npm run typecheck    # Type checking
npm run build        # Production build
```

**Tests:** No test suite exists yet. Use `pytest` under `tests/` if adding tests.

## Architecture

### LangGraph Pipeline (docuflow/graph/)

The core is a `StateGraph` using `DocuFlowState` (in `graph/state.py`). Four sub-graphs in `graph/builder.py` enable staged execution:

1. **`build_init_graph`** — `load_documents` → `generate_glossary` → `generate_dag` → `initialize_status`
2. **`build_generation_graph`** — Parallel module processing via LangGraph Send API: finds modules with satisfied DAG dependencies, dispatches them in parallel, collects results in a loop
3. **`build_overview_graph`** — `extract_summaries` → `generate_system_design` → `generate_interface_design` → `generate_database_design`
4. **`build_assembly_graph`** — Produces final markdown document

**Critique loop** (Phase 2): After module generation, `critique_module` scores the design. If below threshold, `regenerate_module` loops back (up to max iterations). Configured via `DOCUFLOW_CRITIQUE_*` env vars.

**Edge routers** in `graph/edges.py`: `module_router`, `generation_router`, `parallel_module_router`, `critique_router` handle conditional branching.

### Package Roles

| Package | Role |
|---------|------|
| `docuflow/graph/` | LangGraph nodes, edges, state, orchestrator, builder |
| `docuflow/llm/` | Azure OpenAI client with structured Pydantic outputs |
| `docuflow/parsers/` | PDF/DOCX parsing, image extraction + GPT descriptions |
| `docuflow/core/` | Pydantic Settings config, data models |
| `docuflow/cli/` | Typer CLI entry point |
| `docuflow/api/` | FastAPI REST + WebSocket (real-time progress) |
| `docuflow/frontend/` | Vue 3 + Element Plus + Pinia SPA |

### LLM Integration

All calls use Azure OpenAI endpoints exclusively. Models: `gpt-5.2`, `gpt-5.1`, `deepseek-v3.2`. Each requires its own `*_AZURE_OPENAI_ENDPOINT`, `*_AZURE_OPENAI_DEPLOYMENT`, `*_AZURE_OPENAI_API_VERSION` env vars.

### Data Layout

```
data/input/<project>/              ← source requirement docs
data/<project>/<model>/workspace/  ← glossary, DAG, module designs, critique logs, status.yaml
data/<project>/<model>/output/     ← final_design_document.md
```

## Code Style

- Python: 4-space indent, type hints, `snake_case` functions, `PascalCase` classes, prefer `pathlib.Path`
- Vue/TS: 2-space indent, API calls in `frontend/src/api/`
- Commits: short imperative Chinese subjects (e.g., "新增 API 端点：projects")
- No formatter enforced; match neighboring code style

## Environment

Copy `.env.example` → `.env` with Azure OpenAI credentials. `DOCUFLOW_AZURE_OPENAI_API_KEY` is required.
