# Scraper SRE Platform (MVP)

This is a prototype "SRE Layer" for web scraping operations. It provides observability (monitoring success rates, schema drift) and a self-healing mechanism using simulated AI repair.

## Architecture

- **Backend (`backend/`)**: FastAPI backend that ingests run metrics, detects failures, and generates repair suggestions.
- **SDK (`sdk/`)**: Python client library to instrument your scrapers.
- **Demo (`demo/`)**: Example scraper showing the workflow.

## Features

1.  **Observability**: Tracks every scraper run (success/fail, duration, items extracted).
2.  **Schema Drift Detection**: Alerts if the data structure changes (e.g., keys disappear).
3.  **Null Spike Detection**: Alerts if a run returns 0 items when it usually returns data.
4.  **AI Repair Engine**: When a selector breaks, it compares the old HTML snapshot with the new one and generates an LLM prompt to fix the CSS selector.

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the server:
    ```bash
    uvicorn backend.app.main:app --reload
    ```

3.  Run the demo scraper:
    ```bash
    python demo/demo_scraper.py
    ```

## Usage

### Instrumenting a Scraper

```python
from scraper_sre import ScraperObserver

observer = ScraperObserver(scraper_id="your-scraper-id", api_url="http://localhost:8000/api/v1")

with observer.monitor():
    # Your scraping logic here
    # ...
    observer.capture_data(extracted_items)
    observer.capture_snapshot(html_content)
```
