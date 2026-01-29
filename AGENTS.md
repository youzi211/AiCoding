# Repository Guidelines

## Project Structure & Module Organization

- `docuflow/`: Python package (backend + orchestration)
  - `docuflow/cli/`: Typer CLI entry (`docuflow`)
  - `docuflow/api/`: FastAPI service (`docuflow-api`)
  - `docuflow/graph/`: LangGraph workflows and orchestration
  - `docuflow/core/`: configuration, settings, shared models
  - `docuflow/llm/`: LLM clients/integrations (Azure OpenAI)
  - `docuflow/parsers/`: PDF/DOCX parsing and content extraction
  - `docuflow/utils/`: shared helpers (logging, etc.)
- `docuflow/frontend/`: Vue 3 + Vite UI (TypeScript, Element Plus)
- `data/`: local inputs/outputs (generated workspaces and final docs; avoid committing)
- `tests/`: optional `pytest` tests (not required, but preferred for new code paths)
- `.env.example`: environment variable template (copy to `.env`, never commit secrets)

## Build, Test, and Development Commands

Backend (Python 3.11+):

- Create venv: `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
- Install (editable): `pip install -e .` (or `uv sync` if you use `uv`)
- CLI help: `docuflow --help`
- Run end-to-end: `docuflow all -p <project> -m gpt-5.2`
- Run API: `docuflow-api` (docs at `http://localhost:8000/docs`)

Frontend:

- `cd docuflow/frontend`
- Install: `npm ci`
- Dev server: `npm run dev`
- Typecheck/build: `npm run typecheck` / `npm run build`

## Coding Style & Naming Conventions

- Python: 4-space indentation, type hints where practical, `snake_case` functions, `PascalCase` classes, prefer `pathlib.Path`.
- Vue/TS: follow existing 2-space indentation; keep API calls in `docuflow/frontend/src/api/`.
- Keep changes focused and consistent with neighboring files (no formatter is enforced yet).

## Testing Guidelines

- No dedicated test suite is checked in. If you add tests, prefer `pytest` under `tests/` (e.g., `tests/test_cli_smoke.py`).
- Keep tests small and deterministic; cover new logic and error handling paths.

## Commit & Pull Request Guidelines

- Commit subjects are short and descriptive (often Chinese), imperative, and scoped (e.g., “新增 API 端点：projects”).
- PRs should include: what/why, steps to verify, linked issues (if any), and screenshots for UI changes.
- Do not commit secrets (`.env` is ignored) or generated artifacts under `data/` or frontend build outputs.

## Agent-Specific Notes

- If there are nested `AGENTS.md` files, follow the most specific one for files you touch.
