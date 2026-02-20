import os
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from .models import Scraper, ScraperRun, Alert, ScraperConfig

# Get MongoDB URL from env.
# Use "mock://" to run in-memory for testing/demo without Mongo.
MONGODB_URL = os.getenv("MONGODB_URL", "mock://")
DB_NAME = "scraper_sre"

client = None
db = None

# In-memory storage for mock mode
mock_storage = {
    "scrapers": [],
    "runs": [],
    "alerts": []
}

async def connect_to_mongo():
    global client, db
    if MONGODB_URL.startswith("mock://"):
        print("Using In-Memory Mock Database")
        return

    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        print(f"Connected to MongoDB at {MONGODB_URL}")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

async def close_mongo_connection():
    global client
    if client:
        client.close()

# --- Scraper Operations ---

async def create_scraper(scraper: Scraper):
    if MONGODB_URL.startswith("mock://"):
        mock_storage["scrapers"].append(scraper.model_dump(mode='json'))
        return
    await db.scrapers.insert_one(scraper.model_dump(mode='json'))

async def get_scraper(scraper_id: str) -> Optional[Scraper]:
    if MONGODB_URL.startswith("mock://"):
        for doc in mock_storage["scrapers"]:
            if doc["id"] == scraper_id:
                return Scraper(**doc)
        return None
    doc = await db.scrapers.find_one({"id": scraper_id})
    if doc:
        return Scraper(**doc)
    return None

async def get_all_scrapers() -> List[Scraper]:
    if MONGODB_URL.startswith("mock://"):
        return [Scraper(**doc) for doc in mock_storage["scrapers"]]
    cursor = db.scrapers.find({})
    scrapers = []
    async for doc in cursor:
        scrapers.append(Scraper(**doc))
    return scrapers

# --- Run Operations ---

async def save_run(run: ScraperRun):
    if MONGODB_URL.startswith("mock://"):
        mock_storage["runs"].append(run.model_dump(mode='json'))
        return
    await db.runs.insert_one(run.model_dump(mode='json'))

async def get_last_successful_run(scraper_id: str, exclude_run_id: Optional[str] = None) -> Optional[ScraperRun]:
    if MONGODB_URL.startswith("mock://"):
        # Filter and sort in memory
        candidates = [r for r in mock_storage["runs"]
                      if r["scraper_id"] == scraper_id and r["status"] == "SUCCESS"]
        if exclude_run_id:
            candidates = [r for r in candidates if r["id"] != exclude_run_id]

        # Sort by timestamp desc
        candidates.sort(key=lambda x: x["timestamp"], reverse=True)

        if candidates:
            return ScraperRun(**candidates[0])
        return None

    query = {"scraper_id": scraper_id, "status": "SUCCESS"}
    if exclude_run_id:
        query["id"] = {"$ne": exclude_run_id}

    doc = await db.runs.find_one(
        query,
        sort=[("timestamp", -1)]
    )
    if doc:
        return ScraperRun(**doc)
    return None

async def get_runs(scraper_id: str, limit: int = 20) -> List[ScraperRun]:
    if MONGODB_URL.startswith("mock://"):
        candidates = [r for r in mock_storage["runs"] if r["scraper_id"] == scraper_id]
        candidates.sort(key=lambda x: x["timestamp"], reverse=True)
        return [ScraperRun(**doc) for doc in candidates[:limit]]

    cursor = db.runs.find({"scraper_id": scraper_id}).sort("timestamp", -1).limit(limit)
    runs = []
    async for doc in cursor:
        runs.append(ScraperRun(**doc))
    return runs

# --- Alert Operations ---

async def save_alert(alert: Alert):
    if MONGODB_URL.startswith("mock://"):
        mock_storage["alerts"].append(alert.model_dump(mode='json'))
        return
    await db.alerts.insert_one(alert.model_dump(mode='json'))

async def get_alerts(scraper_id: str, limit: int = 20) -> List[Alert]:
    if MONGODB_URL.startswith("mock://"):
        candidates = [r for r in mock_storage["alerts"] if r["scraper_id"] == scraper_id]
        candidates.sort(key=lambda x: x["timestamp"], reverse=True)
        return [Alert(**doc) for doc in candidates[:limit]]

    cursor = db.alerts.find({"scraper_id": scraper_id}).sort("timestamp", -1).limit(limit)
    alerts = []
    async for doc in cursor:
        alerts.append(Alert(**doc))
    return alerts
