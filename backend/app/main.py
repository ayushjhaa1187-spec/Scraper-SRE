import os
import motor.motor_asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from .models import Scraper, ScraperConfig, ScraperRun, Alert, RepairSuggestion, RunStatus, DriftType
from .database import (
    connect_to_mongo,
    close_mongo_connection,
    create_scraper as db_create_scraper,
    get_scraper as db_get_scraper,
    save_run as db_save_run,
    get_last_successful_run as db_get_last_successful_run,
    save_alert as db_save_alert,
    get_runs as db_get_runs,
    get_all_scrapers as db_get_all_scrapers,
    get_alerts as db_get_alerts
)
from .analyzer import detect_drift
from .repair import generate_fix_prompt, mock_llm_repair

app = FastAPI(title="Scraper SRE Platform")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev/demo. In production, restrict this.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

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

@app.get("/")
async def root():
    return {"message": "Scraper SRE Platform API is running"}

@app.post("/api/v1/register", response_model=Scraper)
async def register_scraper(req: RegisterRequest):
    scraper_id = str(uuid.uuid4())
    config = ScraperConfig(name=req.name, target_url=req.target_url, selectors=req.selectors)
    scraper = Scraper(id=scraper_id, config=config, created_at=datetime.now())
    await db_create_scraper(scraper)
    return scraper

@app.get("/api/v1/scrapers", response_model=List[Scraper])
async def list_scrapers():
    return await db_get_all_scrapers()

@app.get("/api/v1/scrapers/{scraper_id}", response_model=Scraper)
async def get_scraper_details(scraper_id: str):
    scraper = await db_get_scraper(scraper_id)
    if not scraper:
        raise HTTPException(status_code=404, detail="Scraper not found")
    return scraper

@app.get("/api/v1/scrapers/{scraper_id}/runs", response_model=List[ScraperRun])
async def list_runs(scraper_id: str):
    return await db_get_runs(scraper_id)

@app.get("/api/v1/scrapers/{scraper_id}/alerts", response_model=List[Alert])
async def list_alerts(scraper_id: str):
    return await db_get_alerts(scraper_id)

@app.post("/api/v1/ingest")
async def ingest_run(req: IngestRunRequest, background_tasks: BackgroundTasks):
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
    await db_save_run(run)

    # 2. Analyze asynchronously
    background_tasks.add_task(analyze_run, run)

    return {"run_id": run_id, "status": "processing"}

async def analyze_run(run: ScraperRun):
    logger.info(f"Analyzing run {run.id} for scraper {run.scraper_id}")

    # Get last successful run for comparison (excluding the current one)
    last_run = await db_get_last_successful_run(run.scraper_id, exclude_run_id=run.id)

    if not last_run:
        logger.info("No previous successful run found for comparison.")
        # If run failed, we still might want to alert
        if run.status == RunStatus.FAILURE:
            alert = Alert(
                id=str(uuid.uuid4()),
                scraper_id=run.scraper_id,
                run_id=run.id,
                type=DriftType.VALUE_DISTRIBUTION,
                message=f"Run failed: {run.error_message}",
                severity="HIGH",
                timestamp=datetime.now()
            )
            await db_save_alert(alert)
        return

    # Detect Drift
    alerts = detect_drift(run, last_run)
    for alert in alerts:
        logger.warning(f"Drift Detected: {alert.message}")
        await db_save_alert(alert)

        # Trigger Repair if it's a schema change or null spike
        if alert.type in [DriftType.SCHEMA_CHANGE, DriftType.NULL_SPIKE]:
            await trigger_repair(run, last_run, alert)

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
        await db_save_alert(alert)
        # Trigger Repair logic if we have snapshots
        if last_run and run.html_snapshot:
             await trigger_repair(run, last_run, alert)

async def trigger_repair(current_run: ScraperRun, last_run: ScraperRun, alert: Alert):
    logger.info("Triggering AI Repair...")

    scraper = await db_get_scraper(current_run.scraper_id)
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
