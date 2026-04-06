"""
VerifyPulse Database Manager
SQLite storage for articles, sources, and fetch history.
Replaces the in-memory store from Day 1.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from app.config import DATABASE_PATH, RSS_SOURCES


# ─── CONNECTION MANAGER ─────────────────────────────────────────
@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # return dicts instead of tuples
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── SCHEMA SETUP ───────────────────────────────────────────────
def init_database():
    """
    Create all tables if they don't exist.
    Safe to call multiple times — uses IF NOT EXISTS.
    """
    with get_db() as conn:
        conn.executescript("""
            -- Sources table: tracks each news source and its credibility
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT,
                region TEXT DEFAULT 'global',
                credibility_score INTEGER DEFAULT 50,
                source_type TEXT DEFAULT 'unknown',
                article_count INTEGER DEFAULT 0,
                last_fetched_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            -- Articles table: every article we've ever fetched
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                source_id TEXT NOT NULL,
                source_name TEXT,
                published_at TEXT,
                summary TEXT,
                region TEXT DEFAULT 'global',
                credibility_score INTEGER DEFAULT 50,
                fetched_at TEXT DEFAULT (datetime('now')),
                cluster_id TEXT,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            );

            -- Fetch history: log of every fetch cycle
            CREATE TABLE IF NOT EXISTS fetch_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fetched_at TEXT DEFAULT (datetime('now')),
                rss_count INTEGER DEFAULT 0,
                gdelt_count INTEGER DEFAULT 0,
                total_new INTEGER DEFAULT 0,
                total_duplicate INTEGER DEFAULT 0
            );

            -- Indexes for fast queries
            CREATE INDEX IF NOT EXISTS idx_articles_region
                ON articles(region);
            CREATE INDEX IF NOT EXISTS idx_articles_source
                ON articles(source_id);
            CREATE INDEX IF NOT EXISTS idx_articles_published
                ON articles(published_at DESC);
            CREATE INDEX IF NOT EXISTS idx_articles_fetched
                ON articles(fetched_at DESC);
            CREATE INDEX IF NOT EXISTS idx_articles_cluster
                ON articles(cluster_id);
        """)

        # Seed source credibility table from config
        _seed_sources(conn)

    print("  ✓ Database initialized")


def _seed_sources(conn: sqlite3.Connection):
    """Insert or update configured RSS sources."""
    for source in RSS_SOURCES:
        conn.execute("""
            INSERT INTO sources (id, name, url, region, credibility_score, source_type)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                credibility_score = excluded.credibility_score,
                name = excluded.name
        """, (
            source["id"],
            source["name"],
            source["url"],
            source["region"],
            source["credibility_score"],
            source["type"],
        ))

    # Add a generic GDELT source entry
    conn.execute("""
        INSERT OR IGNORE INTO sources (id, name, region, credibility_score, source_type)
        VALUES ('gdelt', 'GDELT Project', 'global', 65, 'aggregator')
    """)


# ─── ARTICLE OPERATIONS ────────────────────────────────────────
def insert_articles(articles: list[dict]) -> dict:
    """
    Insert articles into the database, skipping duplicates.

    Args:
        articles: List of article dicts (from Article.model_dump())

    Returns:
        Dict with counts: {"new": int, "duplicate": int}
    """
    new_count = 0
    dup_count = 0

    with get_db() as conn:
        for article in articles:
            try:
                conn.execute("""
                    INSERT INTO articles
                        (id, title, url, source_id, source_name,
                         published_at, summary, region, credibility_score, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.get("id"),
                    article.get("title"),
                    article.get("url"),
                    article.get("source_id"),
                    article.get("source_name"),
                    _format_dt(article.get("published_at")),
                    article.get("summary"),
                    article.get("region", "global"),
                    article.get("credibility_score", 50),
                    _format_dt(article.get("fetched_at")),
                ))
                new_count += 1
            except sqlite3.IntegrityError:
                # Duplicate URL or ID — skip it
                dup_count += 1

        # Update source article counts
        conn.execute("""
            UPDATE sources SET article_count = (
                SELECT COUNT(*) FROM articles WHERE articles.source_id = sources.id
            ), last_fetched_at = datetime('now')
        """)

    return {"new": new_count, "duplicate": dup_count}


def get_articles(
    region: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    hours: Optional[int] = None,
) -> list[dict]:
    """
    Query articles with optional filters.

    Args:
        region: Filter by region (e.g. 'india', 'east_asia')
        limit: Max articles to return
        offset: Pagination offset
        hours: Only articles from the last N hours

    Returns:
        List of article dicts
    """
    query = "SELECT * FROM articles WHERE 1=1"
    params = []

    if region:
        query += " AND region = ?"
        params.append(region)

    if hours:
        query += " AND fetched_at >= datetime('now', ?)"
        params.append(f"-{hours} hours")

    query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_article_count(region: Optional[str] = None) -> int:
    """Get total article count, optionally filtered by region."""
    query = "SELECT COUNT(*) FROM articles"
    params = []

    if region:
        query += " WHERE region = ?"
        params.append(region)

    with get_db() as conn:
        return conn.execute(query, params).fetchone()[0]


def get_source_stats() -> list[dict]:
    """Get all sources with their article counts."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, name, credibility_score, source_type,
                   article_count, last_fetched_at
            FROM sources
            ORDER BY credibility_score DESC
        """).fetchall()
        return [dict(row) for row in rows]


def get_unique_source_count() -> int:
    """Get number of sources that have at least one article."""
    with get_db() as conn:
        return conn.execute(
            "SELECT COUNT(DISTINCT source_id) FROM articles"
        ).fetchone()[0]


# ─── FETCH LOG ──────────────────────────────────────────────────
def log_fetch(rss_count: int, gdelt_count: int, new: int, duplicate: int):
    """Record a fetch cycle in the log."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO fetch_log (rss_count, gdelt_count, total_new, total_duplicate)
            VALUES (?, ?, ?, ?)
        """, (rss_count, gdelt_count, new, duplicate))


def get_last_fetch() -> Optional[dict]:
    """Get the most recent fetch log entry."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM fetch_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


# ─── HELPERS ────────────────────────────────────────────────────
def _format_dt(value) -> Optional[str]:
    """Convert datetime to ISO string for SQLite storage."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return str(value)
