# AGENTS.md

## Cursor Cloud specific instructions

### Project Overview

VerifyPulse is a real-time news verification dashboard. It has a single FastAPI backend (Python) and a static HTML frontend (no build step).

### Running the Backend

```bash
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- On startup, the app auto-creates a SQLite database (`verifypulse.db`) in the `backend/` directory and begins fetching news every 15 minutes via APScheduler.
- The API docs are available at http://localhost:8000/docs (Swagger UI).
- Some GDELT API requests may return 429 (rate-limited) — this is expected and does not prevent the app from running.

### Running Tests

```bash
cd backend
python3 -m pytest tests/ -v
```

All tests are self-contained and do not require the server to be running.

### Linting

```bash
cd backend
ruff check .
```

Note: The existing codebase has some pre-existing lint warnings (unused imports, f-strings without placeholders). These are in the original code.

### Frontend

The frontend is a single static HTML file at `frontend/index.html`. No build step is needed — it connects to the backend at `localhost:8000`.

### Key Gotchas

- Use `python3` not `python` — the system only has `python3` on PATH.
- The SQLite database file (`verifypulse.db`) is auto-created in the `backend/` working directory on first run.
- RSS feeds (Reuters, AP) may not always return articles depending on feed availability; BBC, Al Jazeera, and NDTV are the most reliable sources.
- GDELT API has aggressive rate limiting — 429 errors are common and handled gracefully.
