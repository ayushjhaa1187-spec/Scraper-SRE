from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from .models import Scraper, ScraperConfig, ScraperRun, Alert, RepairSuggestion, RunStatus, DriftType
from .database import init_db, create_scraper, get_scraper, save_run, get_last_successful_run, save_alert
from .analyzer import detect_drift
from .repair import generate_fix_prompt, mock_llm_repair

app = FastAPI(title="Scraper SRE Platform")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def startup_event():
    init_db()

class RegisterRequest(BaseModel):
    name: str
    target_url: str
    selectors: Dict[str, str]

class IngestRunRequest(BaseModel):
    scraper_id: str
    status: RunStatus
    duration_ms: float
    items_extracted: int
    error_message: Optional[str] = None
    extracted_data_sample: Optional[List[Dict[str, Any]]] = None
    html_snapshot: Optional[str] = None

@app.post("/api/v1/register", response_model=Scraper)
def register_scraper(req: RegisterRequest):
    scraper_id = str(uuid.uuid4())
    config = ScraperConfig(name=req.name, target_url=req.target_url, selectors=req.selectors)
    scraper = Scraper(id=scraper_id, config=config, created_at=datetime.now())
    create_scraper(scraper)
    return scraper

@app.post("/api/v1/ingest")
def ingest_run(req: IngestRunRequest, background_tasks: BackgroundTasks):
    # 1. Save the run
    run_id = str(uuid.uuid4())
    run = ScraperRun(
        id=run_id,
        scraper_id=req.scraper_id,
        timestamp=datetime.now(),
        status=req.status,
        duration_ms=req.duration_ms,
        items_extracted=req.items_extracted,
        error_message=req.error_message,
        extracted_data_sample=req.extracted_data_sample,
        html_snapshot=req.html_snapshot
    )
    save_run(run)

    # 2. Analyze asynchronously (simulated via background task)
    background_tasks.add_task(analyze_run, run)

    return {"run_id": run_id, "status": "processing"}

def analyze_run(run: ScraperRun):
    logger.info(f"Analyzing run {run.id} for scraper {run.scraper_id}")

    # Get last successful run for comparison (excluding the current one)
    last_run = get_last_successful_run(run.scraper_id, exclude_run_id=run.id)

    if not last_run:
        logger.info("No previous successful run found for comparison.")
        return

    # Detect Drift
    alerts = detect_drift(run, last_run)
    for alert in alerts:
        logger.warning(f"Drift Detected: {alert.message}")
        save_alert(alert)

        # Trigger Repair if it's a schema change or null spike
        if alert.type in [DriftType.SCHEMA_CHANGE, DriftType.NULL_SPIKE]:
            trigger_repair(run, last_run, alert)

    # Detect Failure (if status is FAILURE)
    if run.status == RunStatus.FAILURE:
        alert = Alert(
            id=str(uuid.uuid4()),
            scraper_id=run.scraper_id,
            run_id=run.id,
            type=DriftType.VALUE_DISTRIBUTION, # Reusing type
            message=f"Run failed: {run.error_message}",
            severity="HIGH",
            timestamp=datetime.now()
        )
        save_alert(alert)
        # Trigger Repair logic if we have snapshots
        if last_run and run.html_snapshot:
             trigger_repair(run, last_run, alert)

def trigger_repair(current_run: ScraperRun, last_run: ScraperRun, alert: Alert):
    logger.info("Triggering AI Repair...")

    scraper = get_scraper(current_run.scraper_id)
    if not scraper:
        return

    # For each selector in the config, check if we can fix it.
    broken_selectors = []

    if alert.type == DriftType.SCHEMA_CHANGE:
        # Identify missing keys
        curr_keys = set(current_run.extracted_data_sample[0].keys()) if current_run.extracted_data_sample else set()
        last_keys = set(last_run.extracted_data_sample[0].keys()) if last_run.extracted_data_sample else set()
        missing = last_keys - curr_keys

        for key in missing:
            if key in scraper.config.selectors:
                broken_selectors.append((key, scraper.config.selectors[key]))

    elif alert.type == DriftType.NULL_SPIKE:
        # Assume all selectors might be broken
        for key, sel in scraper.config.selectors.items():
             broken_selectors.append((key, sel))

    # Generate Prompts
    for field, selector in broken_selectors:
        # We need the OLD snapshot to show context.
        if last_run.html_snapshot and current_run.html_snapshot:
            prompt = generate_fix_prompt(
                old_html=last_run.html_snapshot,
                new_html=current_run.html_snapshot,
                broken_selector=selector,
                field_name=field
            )

            # Call LLM (Mock)
            suggestion = mock_llm_repair(prompt)

            logger.info(f"AI Suggestion for {field}: {suggestion}")
            # In a real app, save this suggestion to DB.
