from typing import List, Dict, Any, Optional
from .models import ScraperRun, DriftType, Alert
import uuid
from datetime import datetime

def detect_drift(current_run: ScraperRun, last_run: Optional[ScraperRun]) -> List[Alert]:
    alerts = []

    if not last_run:
        return []

    # 1. Check for Null Spike (Empty extraction where previously there was data)
    if (not current_run.extracted_data_sample or len(current_run.extracted_data_sample) == 0) and \
       (last_run.extracted_data_sample and len(last_run.extracted_data_sample) > 0):
        alerts.append(Alert(
            id=str(uuid.uuid4()),
            scraper_id=current_run.scraper_id,
            run_id=current_run.id,
            type=DriftType.NULL_SPIKE,
            message="Extracted 0 items, but previous run extracted items.",
            severity="HIGH",
            timestamp=datetime.now()
        ))
        return alerts

    if not current_run.extracted_data_sample or not last_run.extracted_data_sample:
        return alerts

    # 2. Check for Schema Change (Keys mismatch)
    # We compare the keys of the first item in the sample
    curr_keys = set(current_run.extracted_data_sample[0].keys())
    last_keys = set(last_run.extracted_data_sample[0].keys())

    if curr_keys != last_keys:
        missing = last_keys - curr_keys
        added = curr_keys - last_keys
        message = f"Schema changed. Missing keys: {missing}, Added keys: {added}"
        alerts.append(Alert(
            id=str(uuid.uuid4()),
            scraper_id=current_run.scraper_id,
            run_id=current_run.id,
            type=DriftType.SCHEMA_CHANGE,
            message=message,
            severity="HIGH",
            timestamp=datetime.now()
        ))

    return alerts
