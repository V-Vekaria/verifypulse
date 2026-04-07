# VerifyPulse API Documentation

## Base URL
```
http://localhost:8000
```

## Interactive Docs
Open http://localhost:8000/docs for the Swagger UI playground.

---

## Stories (Core Feature)

### GET /api/stories
Get clustered and scored news stories.

**Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| region | string | all | Filter: global, india, east_asia, americas |
| hours | int | 48 | Time window for clustering |
| min_confidence | float | 0 | Minimum confidence score (0-100) |

**Example Response:**
```json
{
  "count": 15,
  "stories": [
    {
      "cluster_id": "cluster_a1b2c3",
      "title": "India PM Modi visits Japan for bilateral summit",
      "confidence_score": 72.5,
      "confidence_label": "Likely Accurate",
      "confidence_color": "#84cc16",
      "source_count": 3,
      "source_ids": ["reuters", "bbc_world", "ndtv"],
      "regions": ["global", "india"],
      "scoring_breakdown": {
        "source_count": {"value": 3, "points": 25, "max": 40},
        "avg_credibility": {"value": 87, "points": 30.4, "max": 35},
        "source_diversity": {"types": ["wire_service", "broadcaster", "national"], "points": 20, "max": 25}
      }
    }
  ]
}
```

### GET /api/stories/{cluster_id}
Full detail for a single story with all articles and scoring breakdown.

### GET /api/confidence-levels
Returns all confidence level definitions with score ranges and colors.

---

## Data Endpoints

### POST /api/fetch
Manually trigger news fetch from all sources. Also runs automatically every 15 minutes.

### GET /api/articles
Raw articles with optional filters (region, limit, offset, hours).

### GET /api/sources
All configured sources with credibility scores and article counts.

### GET /api/stats
System overview — total articles, active sources, per-region breakdown.

### GET /api/health
Health check with basic stats.

---

## Confidence Scoring

Stories are scored on three factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Source Count | 0-40 pts | How many independent sources report the story |
| Source Credibility | 0-35 pts | Average credibility score of reporting sources |
| Source Diversity | 0-25 pts | Variety of source types (wire, broadcaster, national) |

**Confidence Labels:**
| Score Range | Label | Color |
|-------------|-------|-------|
| 80-100 | Verified | Green |
| 60-79 | Likely Accurate | Lime |
| 40-59 | Developing | Yellow |
| 20-39 | Unverified | Orange |
| 0-19 | Disputed | Red |
