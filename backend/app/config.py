"""
VerifyPulse Configuration
All news sources, credibility scores, and settings in one place.
"""

# ─── NEWS SOURCES ───────────────────────────────────────────────
# Each source has: name, type, url, region, credibility_score (0-100)
#
# Credibility scoring rationale:
#   90-100: Major wire services with strict editorial standards
#   80-89:  Major international broadcasters with editorial oversight
#   70-79:  Reputable national/regional outlets
#   Below 70: Added in Phase 2 with more verification layers

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
]

# ─── GDELT SETTINGS ─────────────────────────────────────────────
GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2"
GDELT_DOC_API = f"{GDELT_BASE_URL}/doc/doc"
GDELT_DEFAULT_PARAMS = {
    "mode": "ArtList",
    "format": "json",
    "maxrecords": 50,
    "timespan": "60min",  # last 60 minutes
}

# ─── REGION MAPPING ─────────────────────────────────────────────
REGIONS = {
    "global": "Global",
    "india": "India",
    "east_asia": "East Asia",
    "americas": "Americas",
}

# Region keywords for GDELT queries
REGION_QUERIES = {
    "india": "India OR Delhi OR Mumbai OR Modi",
    "east_asia": "China OR Japan OR Korea OR Tokyo OR Beijing",
    "americas": "United States OR Washington OR Congress OR Biden",
    "global": "",  # no filter = global
}

# ─── APP SETTINGS ───────────────────────────────────────────────
FETCH_INTERVAL_MINUTES = 15  # how often to pull new articles
DATABASE_PATH = "verifypulse.db"
MAX_ARTICLES_PER_FETCH = 100
