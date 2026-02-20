import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from .models import Scraper, ScraperRun, Alert, RepairSuggestion, ScraperConfig

DB_FILE = "scraper_sre.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scrapers (
        id TEXT PRIMARY KEY,
        name TEXT,
        config TEXT,
        created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS runs (
        id TEXT PRIMARY KEY,
        scraper_id TEXT,
        timestamp TEXT,
        status TEXT,
        duration_ms REAL,
        items_extracted INTEGER,
        error_message TEXT,
        extracted_data_sample TEXT,
        html_snapshot TEXT,
        FOREIGN KEY(scraper_id) REFERENCES scrapers(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id TEXT PRIMARY KEY,
        scraper_id TEXT,
        run_id TEXT,
        type TEXT,
        message TEXT,
        severity TEXT,
        timestamp TEXT,
        FOREIGN KEY(run_id) REFERENCES runs(id)
    )''')
    conn.commit()
    conn.close()

def create_scraper(scraper: Scraper):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO scrapers VALUES (?, ?, ?, ?)",
              (scraper.id, scraper.config.name, scraper.config.model_dump_json(), scraper.created_at.isoformat()))
    conn.commit()
    conn.close()

def get_scraper(scraper_id: str) -> Optional[Scraper]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM scrapers WHERE id = ?", (scraper_id,))
    row = c.fetchone()
    conn.close()
    if row:
        config_data = json.loads(row["config"])
        return Scraper(
            id=row["id"],
            config=ScraperConfig(**config_data),
            created_at=datetime.fromisoformat(row["created_at"])
        )
    return None

def save_run(run: ScraperRun):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (run.id, run.scraper_id, run.timestamp.isoformat(), run.status.value,
               run.duration_ms, run.items_extracted, run.error_message,
               json.dumps(run.extracted_data_sample) if run.extracted_data_sample else None,
               run.html_snapshot))
    conn.commit()
    conn.close()

def get_last_successful_run(scraper_id: str, exclude_run_id: Optional[str] = None) -> Optional[ScraperRun]:
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT * FROM runs
        WHERE scraper_id = ? AND status = 'SUCCESS'
    """
    params = [scraper_id]

    if exclude_run_id:
        query += " AND id != ?"
        params.append(exclude_run_id)

    query += " ORDER BY timestamp DESC LIMIT 1"

    c.execute(query, tuple(params))
    row = c.fetchone()
    conn.close()
    if row:
        return ScraperRun(
            id=row["id"],
            scraper_id=row["scraper_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            status=row["status"],
            duration_ms=row["duration_ms"],
            items_extracted=row["items_extracted"],
            error_message=row["error_message"],
            extracted_data_sample=json.loads(row["extracted_data_sample"]) if row["extracted_data_sample"] else None,
            html_snapshot=row["html_snapshot"]
        )
    return None

def save_alert(alert: Alert):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?)",
              (alert.id, alert.scraper_id, alert.run_id, alert.type.value, alert.message, alert.severity, alert.timestamp.isoformat()))
    conn.commit()
    conn.close()
