# Arabic AI Comic Generator

Generates 3-panel Arabic comics: **OpenAI** produces the ComicScript JSON; **Gemini** generates panel images.

## Setup

```bash
# Python (use uv or pip)
uv sync
# or: pip install -e .

# Copy env
cp .env.example .env
# Add OPENAI_API_KEY and GEMINI_API_KEY
```

Models are set in `src/utils/config.py` (OpenAI text model for the script; Gemini image model for panels). Only API keys come from the environment.

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
  - `src/panel/` — Page layout and assembly
  - `src/utils/` — Config, logger, clients
