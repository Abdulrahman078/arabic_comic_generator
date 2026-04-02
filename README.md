# Arabic AI Comic Generator

Generates 3-panel Arabic comics from story prompts using OpenAI (script) and Gemini (images).

## Setup

```bash
# Python (use uv or pip)
uv sync
# or: pip install -e .

# Copy env
cp .env.example .env
# Add OPENAI_API_KEY, GEMINI_API_KEY (or GOOGLE_API_KEY)
```

**Optional env vars:**
- `LLM_MODEL` — Script model (default: gpt-4o-mini)
- `FONT_PREFERENCE` — amiri | cairo | noto_naskh
- `STYLE_LOCK` — Fixed style suffix for panels
- `ENABLE_CACHE` — 1/0 to cache scripts (default: 1)

The UI uses plain `python` (or `.venv/Scripts/python.exe` on Windows if present) — no `uv run` needed.

## Run

**1. Start the UI (spawns Python worker on demand):**
```bash
cd ui && npm install && npm run dev
```

**2. Open http://localhost:3000**

The UI spawns the Python pipeline as a subprocess when you click Generate. No separate server.

## CLI (no UI)

```bash
uv run comic_pipeline
```

## Structure

- `ui/` — Next.js frontend (spawns Python worker via API route)
- `src/` — All Python logic
  - `src/pipeline/main_pipeline.py` — Pipeline orchestration
  - `src/generation/` — Script + images
  - `src/panel/` — Bubbles, layout
  - `src/utils/` — Config, logger, clients
