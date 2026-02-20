from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class RunStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

class DriftType(str, Enum):
    SCHEMA_CHANGE = "SCHEMA_CHANGE"
    VALUE_DISTRIBUTION = "VALUE_DISTRIBUTION"
    NULL_SPIKE = "NULL_SPIKE"

class ScraperConfig(BaseModel):
    name: str
    target_url: str
    selectors: Dict[str, str]  # e.g. {"price": ".price", "title": "h1"}

class Scraper(BaseModel):
    id: str
    config: ScraperConfig
    created_at: datetime

class ScraperRun(BaseModel):
    id: str
    scraper_id: str
    timestamp: datetime
    status: RunStatus
    duration_ms: float
    items_extracted: int
    error_message: Optional[str] = None
    extracted_data_sample: Optional[List[Dict[str, Any]]] = None
    html_snapshot: Optional[str] = None # Base64 or raw HTML string

class Alert(BaseModel):
    id: str
    scraper_id: str
    run_id: str
    type: DriftType
    message: str
    severity: str # "HIGH", "MEDIUM", "LOW"
    timestamp: datetime

class RepairSuggestion(BaseModel):
    id: str
    alert_id: str
    field_name: str
    old_selector: str
    suggested_selector: str
    confidence_score: float
    diff_summary: str
