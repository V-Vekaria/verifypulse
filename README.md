# VerifyPulse 🔍

**Real-time news verification dashboard that scores breaking news by trustworthiness.**

VerifyPulse aggregates news from multiple independent sources, clusters related stories, and calculates a confidence score based on how many credible outlets corroborate each claim. Instead of telling you what's true, it shows you the evidence — so you can decide.

> Built as a solo founder prototype in 7 days. 100% free tech stack.

---

## How It Works

```
  RSS Feeds (Reuters, AP, BBC, Al Jazeera, NDTV)
  + GDELT Global News Database
         │
         ▼
  ┌─────────────────┐
  │  DATA PIPELINE   │  Fetches every 15 min, deduplicates
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │  CLUSTERING      │  TF-IDF + cosine similarity groups
  │  ENGINE          │  related articles into story clusters
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │  CONFIDENCE      │  3-factor scoring: source count,
  │  SCORER          │  credibility, source diversity
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │  REST API        │  FastAPI with auto-generated docs
  │  (FastAPI)       │  at /docs
  └────────┬────────┘
           ▼
  ┌─────────────────┐
  │  DASHBOARD       │  Live feed with confidence badges,
  │  (HTML/JS)       │  filters, and "Why we trust this"
  └─────────────────┘
```

## Confidence Scoring

Each story is scored on three factors:

| Factor | Weight | What It Measures |
|--------|--------|-----------------|
| **Source Count** | 0-40 pts | How many independent sources report the story |
| **Source Credibility** | 0-35 pts | Average credibility of reporting sources |
| **Source Diversity** | 0-25 pts | Variety of source types (wire service, broadcaster, national) |

The combined score maps to a confidence label:

| Score | Label | Meaning |
|-------|-------|---------|
| 80-100 | **Verified** | Multiple independent credible sources confirm |
| 60-79 | **Likely Accurate** | Strong sourcing, not fully independently confirmed |
| 40-59 | **Developing** | Some corroboration, story still evolving |
| 20-39 | **Unverified** | Limited sources, insufficient evidence |
| 0-19 | **Disputed** | Single source or contradictory reports |

## Tech Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| Backend | Python 3.11 + FastAPI | Free |
| Database | SQLite (WAL mode) | Free |
| NLP | scikit-learn TF-IDF | Free |
| Data Sources | RSS feeds + GDELT API | Free |
| Frontend | Vanilla HTML/CSS/JS | Free |
| Fonts | DM Sans + IBM Plex Mono | Free |

**Total cost: $0/month**

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API starts at http://localhost:8000 with auto-generated docs at http://localhost:8000/docs.

On first run, it creates a SQLite database and begins fetching news automatically every 15 minutes.

### Frontend
```bash
# Just open the file in your browser
open frontend/index.html     # macOS
start frontend/index.html    # Windows
```

The dashboard connects to `localhost:8000` and displays stories with confidence scores.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stories` | Clustered stories with confidence scores |
| GET | `/api/stories/{id}` | Story detail with full scoring breakdown |
| GET | `/api/confidence-levels` | Confidence level definitions |
| POST | `/api/fetch` | Manually trigger news fetch |
| GET | `/api/articles` | Raw articles with filters |
| GET | `/api/sources` | Source credibility table |
| GET | `/api/stats` | System overview |

Full documentation: [docs/API.md](docs/API.md)

## Project Structure

```
verifypulse/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifecycle
│   │   ├── config.py            # Sources, regions, settings
│   │   ├── models/              # Pydantic data models
│   │   ├── routers/
│   │   │   ├── stories.py       # /api/stories endpoints
│   │   │   └── data.py          # /api/articles, sources, stats
│   │   └── services/
│   │       ├── rss_fetcher.py   # RSS feed parser
│   │       ├── gdelt_client.py  # GDELT API client
│   │       ├── database.py      # SQLite operations
│   │       ├── dedup.py         # Title similarity dedup
│   │       ├── clustering.py    # TF-IDF story clustering
│   │       ├── confidence.py    # 3-factor confidence scoring
│   │       └── scheduler.py     # Auto-fetch every 15 min
│   ├── tests/
│   │   └── test_clustering.py   # Unit tests
│   └── requirements.txt
├── frontend/
│   └── index.html               # Dashboard (single file, no build)
├── docs/
│   └── API.md                   # API documentation
├── Dockerfile
└── README.md
```

## Future Roadmap (Phase 2)

- [ ] LLM-powered claim extraction (Claude API)
- [ ] Multilingual support (Hindi + more via XLM-RoBERTa)
- [ ] Semantic clustering with sentence-transformers
- [ ] Story timeline tracking (how stories evolve over time)
- [ ] Daily misinformation report generator
- [ ] Deepfake/image manipulation detection
- [ ] Browser extension for inline verification

## Development Timeline

| Day | What Was Built | Commits |
|-----|---------------|---------|
| 1 | Project setup, RSS parser, GDELT client | 4 |
| 2 | SQLite database, deduplication, auto-scheduler | 4 |
| 3 | TF-IDF clustering, confidence scoring, tests | 4 |
| 4 | API routers, documentation | 3 |
| 5 | Frontend dashboard with live feed | 1 |
| 6 | Source timeline, score ring, summary bar | 2 |
| 7 | README, Dockerfile, final polish | 2 |

## License

MIT

## Author

Solo founder prototype — built to demonstrate that news verification can be automated, transparent, and free.
