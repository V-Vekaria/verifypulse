# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

VerifyPulse is a real-time news verification dashboard. Single Python backend (FastAPI + SQLite) with a vanilla HTML/JS frontend. See `README.md` for full architecture.

### Running services

- **Backend**: `cd backend && python3 -m uvicorn app.main:app --reload --port 8000`
  - On first startup, the app runs an initial fetch from RSS feeds and GDELT which can take 30-60 seconds (GDELT often returns 429s or timeouts; this is expected). The server only starts accepting requests after this completes.
  - SQLite DB is auto-created in `backend/` on first run. No separate database setup needed.
- **Frontend**: Serve `frontend/index.html` via any static file server, e.g. `cd frontend && python3 -m http.server 3000`. The frontend connects to `localhost:8000`.

### Tests

```bash
cd backend && python3 -m pytest tests/ -v
```

All 17 unit tests cover clustering and confidence scoring logic. No external services needed for tests.

### Linting

No linter is configured in the repo. Code follows PEP 8 conventions per `CONTRIBUTING.md`.

### Key caveats

- `~/.local/bin` must be on `PATH` for `uvicorn`/`pytest` after pip install (user-level install).
- Some RSS feeds (Reuters, AP) may fail due to DNS or format issues — this is expected and non-blocking. The app works with whatever feeds succeed.
- GDELT API often returns 429 (rate limit) — the app handles this gracefully and continues without GDELT data.
- There is no build step for the frontend — it's a single `index.html` file.
