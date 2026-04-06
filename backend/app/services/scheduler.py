"""
VerifyPulse Scheduler
Automatically fetches news every 15 minutes using APScheduler.
No manual triggering needed — it runs in the background.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from app.config import FETCH_INTERVAL_MINUTES
from app.services.rss_fetcher import fetch_all_rss
from app.services.gdelt_client import fetch_gdelt_by_regions
from app.services.database import insert_articles, log_fetch
from app.services.dedup import deduplicate_articles, get_existing_titles_from_db


# ─── GLOBAL SCHEDULER ──────────────────────────────────────────
scheduler = BackgroundScheduler()


def scheduled_fetch():
    """
    The main fetch job that runs every FETCH_INTERVAL_MINUTES.
    Pulls from all sources, deduplicates, and stores in SQLite.
    """
    print(f"\n⏰ [{datetime.now().strftime('%H:%M:%S')}] Scheduled fetch starting...")

    try:
        # Step 1: Fetch from all sources
        rss_articles = fetch_all_rss()
        gdelt_articles = fetch_gdelt_by_regions()
        all_articles = rss_articles + gdelt_articles

        print(f"  📥 Fetched: {len(rss_articles)} RSS + {len(gdelt_articles)} GDELT = {len(all_articles)} total")

        # Step 2: Deduplicate against existing database
        existing_titles = get_existing_titles_from_db()
        unique, duplicates = deduplicate_articles(all_articles, existing_titles)

        print(f"  🔍 Dedup: {len(unique)} new, {len(duplicates)} duplicates filtered")

        # Step 3: Store unique articles in database
        if unique:
            article_dicts = [a.model_dump() for a in unique]
            result = insert_articles(article_dicts)
            print(f"  💾 Stored: {result['new']} inserted, {result['duplicate']} DB duplicates")
        else:
            result = {"new": 0, "duplicate": 0}
            print("  💤 No new articles to store")

        # Step 4: Log the fetch cycle
        log_fetch(
            rss_count=len(rss_articles),
            gdelt_count=len(gdelt_articles),
            new=result["new"],
            duplicate=len(duplicates) + result["duplicate"],
        )

        print(f"  ✅ Fetch complete\n")

    except Exception as e:
        print(f"  ❌ Fetch failed: {e}\n")


def start_scheduler():
    """
    Start the background scheduler.
    Runs an immediate fetch, then schedules recurring fetches.
    """
    if scheduler.running:
        print("  ⚠ Scheduler already running")
        return

    # Run immediately on startup
    print("🚀 Running initial fetch...")
    scheduled_fetch()

    # Schedule recurring fetches
    scheduler.add_job(
        scheduled_fetch,
        "interval",
        minutes=FETCH_INTERVAL_MINUTES,
        id="news_fetch",
        replace_existing=True,
    )
    scheduler.start()
    print(f"📅 Scheduler started — fetching every {FETCH_INTERVAL_MINUTES} minutes")


def stop_scheduler():
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("🛑 Scheduler stopped")
