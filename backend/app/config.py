"""
VerifyPulse Configuration
All news sources, credibility scores, and settings in one place.
"""

# ─── NEWS SOURCES ───────────────────────────────────────────────
RSS_SOURCES = [
    {
        "id": "reuters",
        "name": "Reuters",
        "url": "https://feeds.reuters.com/reuters/topNews",
        "region": "global",
        "credibility_score": 95,
        "type": "wire_service",
    },
    {
        "id": "ap_news",
        "name": "Associated Press",
        "url": "https://rsshub.app/apnews/topics/apf-topnews",
        "region": "global",
        "credibility_score": 95,
        "type": "wire_service",
    },
    {
        "id": "bbc_world",
        "name": "BBC World",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "region": "global",
        "credibility_score": 88,
        "type": "broadcaster",
    },
    {
        "id": "aljazeera",
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "region": "global",
        "credibility_score": 82,
        "type": "broadcaster",
    },
    {
        "id": "ndtv",
        "name": "NDTV",
        "url": "https://feeds.feedburner.com/ndtvnews-top-stories",
        "region": "india",
        "credibility_score": 78,
        "type": "national",
    },
    # ── Day 5: Hindi sources ─────────────────────────────────────
    {
        "id": "ndtv_hindi",
        "name": "NDTV Hindi",
        "url": "https://feeds.feedburner.com/ndtvkhabar-latest",
        "region": "india",
        "credibility_score": 75,
        "type": "national",
        "language": "hi",
    },
    {
        "id": "aaj_tak",
        "name": "Aaj Tak",
        "url": "https://aajtak.intoday.in/rss/homepage.xml",
        "region": "india",
        "credibility_score": 72,
        "type": "national",
        "language": "hi",
    },
]

# ─── GDELT SETTINGS ─────────────────────────────────────────────
GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2"
GDELT_DOC_API = f"{GDELT_BASE_URL}/doc/doc"
GDELT_DEFAULT_PARAMS = {
    "mode": "ArtList",
    "format": "json",
    "maxrecords": 50,
    "timespan": "60min",
}

# ─── REGION MAPPING ─────────────────────────────────────────────
REGIONS = {
    "global": "Global",
    "india": "India",
    "east_asia": "East Asia",
    "americas": "Americas",
}

REGION_QUERIES = {
    "india": "India OR Delhi OR Mumbai OR Modi",
    "east_asia": "China OR Japan OR Korea OR Tokyo OR Beijing",
    "americas": "United States OR Washington OR Congress OR Biden",
    "global": "",
}

# ─── APP SETTINGS ───────────────────────────────────────────────
FETCH_INTERVAL_MINUTES = 15
DATABASE_PATH = "verifypulse.db"
MAX_ARTICLES_PER_FETCH = 100

# ─── CLUSTERING SETTINGS ────────────────────────────────────────
# Multilingual MiniLM supports 50+ languages including Hindi
# Same threshold works for cross-language clustering
CLUSTER_SIMILARITY_THRESHOLD = 0.55
CLUSTER_WINDOW_HOURS = 48

# ─── EMBEDDING MODEL ────────────────────────────────────────────
# Day 5: swapped to multilingual model
# paraphrase-multilingual-MiniLM-L12-v2 supports Hindi + English cross-clustering
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"