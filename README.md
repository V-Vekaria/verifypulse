# VerifyPulse 🔍

**Real-time news verification dashboard that scores breaking news by trustworthiness.**

VerifyPulse aggregates news from multiple independent sources, clusters related stories, and calculates a confidence score based on how many credible outlets corroborate each claim. Instead of telling you what's true, it shows you the evidence — so you can decide.

## 🚀 What It Does

- Pulls live news from 5+ independent sources (Reuters, AP, BBC, Al Jazeera, NDTV) + GDELT global database
- Groups related articles into story clusters using text similarity
- Scores each story's reliability based on source count, source credibility, and claim consistency
- Displays a live dashboard with color-coded confidence badges

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js)                 │
│  Live Feed  │  Story Detail  │  Region Filter        │
└──────────────────────┬───────────────────────────────┘
                       │ REST API
┌──────────────────────┴───────────────────────────────┐
│                  BACKEND (FastAPI)                    │
│  /api/stories  │  /api/stories/{id}  │  /api/health  │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────┴───────────────────────────────┐
│              VERIFICATION ENGINE                     │
│  RSS Fetcher → Dedup → Clustering → Confidence Score │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────┴───────────────────────────────┐
│                  DATA LAYER (SQLite)                  │
│  articles  │  sources  │  story_clusters  │  claims  │
└──────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| Backend | Python + FastAPI | Free |
| Database | SQLite | Free |
| NLP | scikit-learn (TF-IDF) | Free |
| Data Sources | RSS + GDELT | Free |
| Frontend | Next.js + Tailwind | Free |
| Hosting | Vercel + Docker | Free tier |

## 📦 Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m app.main

# Frontend (coming Day 5)
cd frontend
npm install
npm run dev
```

## 🗓️ Development Roadmap

- [x] **Day 1** — Project setup, RSS parser, GDELT client
- [ ] **Day 2** — Database schema, deduplication, scheduled fetching
- [ ] **Day 3** — Story clustering, confidence scoring
- [ ] **Day 4** — REST API endpoints
- [ ] **Day 5** — Frontend dashboard core
- [ ] **Day 6** — Story detail page, source transparency
- [ ] **Day 7** — Polish, deploy, documentation

## 📄 License

MIT

## 👤 Author

Solo founder project — built in 7 days as a prototype.
