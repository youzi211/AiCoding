# Repository Guidelines

## Project Structure

- `docuflow/`: Python package (backend + orchestration)
  - `docuflow/cli/`: Typer CLI entry (`docuflow`)
  - `docuflow/api/`: FastAPI service (`docuflow-api`)
  - `docuflow/graph/`: LangGraph workflows and orchestration
  - `docuflow/core/`: configuration, settings, shared models
  - `docuflow/llm/`: LLM clients/integrations (Azure OpenAI)
  - `docuflow/parsers/`: PDF/DOCX parsing and content extraction
  - `docuflow/utils/`: shared helpers (logging, etc.)
- `docuflow/frontend/`: Vue 3 + Vite UI (TypeScript, Element Plus)
- `data/`: local inputs/outputs (generated project workspaces and final docs)
- `.env.example`: backend environment variable template (copy to `.env`)

## Build, Test, and Development Commands

Backend (Python 3.11+):

- Create venv: `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
- Install editable: `pip install -e .` (or `uv sync` if you use `uv`)
- CLI help: `docuflow --help`
- Run end-to-end: `docuflow all -p <project> -m gpt-5.2`
- Run API: `docuflow-api` (serves docs at `http://localhost:8000/docs`)

Frontend:

- `cd docuflow/frontend`
- Install deps: `npm ci`
- Dev server: `npm run dev`
- Typecheck/build: `npm run typecheck` / `npm run build`

## Coding Style & Naming Conventions

- Python: 4-space indentation, type hints where practical, `snake_case` for functions, `PascalCase` for classes, prefer `pathlib.Path`.
- Vue/TS: follow existing 2-space indentation; keep API calls in `docuflow/frontend/src/api/`.
- Keep changes focused and consistent with neighboring files (no formatter is enforced in this repo yet).

## Testing Guidelines

- A dedicated test suite is not currently checked in.
- If you add tests, prefer `pytest` and place them under `tests/` (e.g., `tests/test_cli_smoke.py`), and ensure new code paths have basic coverage.

## Commit & Pull Request Guidelines

- History uses short, descriptive (often Chinese) commit subjects; keep messages imperative and scoped (e.g., “新增 API 端点：projects”).
- PRs should include: a clear description, steps to verify, linked issues (if any), and screenshots for UI changes.
- Do not commit secrets (`.env` is ignored). Avoid committing generated `data/` outputs or frontend build artifacts.
