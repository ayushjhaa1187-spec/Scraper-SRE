# Scraper SRE Platform (Full Stack MVP)

This is a comprehensive "SRE Layer" for web scraping operations. It provides observability (monitoring success rates, schema drift) and a self-healing mechanism using simulated AI repair.

## Architecture

- **Backend (`backend/`)**: FastAPI application deployed on Vercel.
  - Ingests run metrics.
  - Detects failures and schema drift.
  - Generates repair suggestions.
  - Uses **MongoDB Atlas** for persistence (with local mock fallback).
- **Frontend (`frontend/`)**: Single Page Dashboard (HTML/JS/Tailwind).
  - Deployed via GitHub Pages or Vercel.
  - Visualizes scrapers, run history, and active alerts.
- **SDK (`sdk/`)**: Python client library to instrument your scrapers.
- **Demo (`demo/`)**: Example scraper showing the workflow.

## Deployment

### 1. Database (MongoDB Atlas)
- Create a Cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
- Get your Connection String (SRV format).
- Allow access from anywhere (0.0.0.0/0) or Vercel IPs.

### 2. Backend (Vercel)
The backend is configured for Vercel Serverless Functions (`vercel.json`).

1.  Install Vercel CLI: `npm i -g vercel`
2.  Deploy:
    ```bash
    vercel
    ```
3.  Set Environment Variable:
    -   `MONGODB_URL`: Your MongoDB Connection String.
    -   (If not set, it defaults to In-Memory Mock Mode).

### 3. Frontend (GitHub Pages / Vercel)
You can deploy the `frontend/` directory as a static site.

-   **Vercel**: `vercel frontend`
-   **GitHub Pages**: Push to `gh-pages` branch or configure Settings to serve `frontend/` directory.
-   **Configuration**: Update the "Backend URL" in the UI to point to your deployed Backend URL.

## Local Development

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Full Stack Demo**:
    ```bash
    ./run_demo.sh
    ```
    This script starts:
    -   Backend API at `http://localhost:8000` (Mock DB Mode by default)
    -   Frontend Dashboard at `http://localhost:8080`
    -   Runs a demo scraper to populate initial data.

3.  **Manual Start**:
    -   Backend: `uvicorn backend.app.main:app --reload`
    -   Frontend: `cd frontend && python -m http.server 8080`

## Features

1.  **Observability**: Tracks every scraper run (success/fail, duration, items extracted).
2.  **Schema Drift Detection**: Alerts if the data structure changes (e.g., keys disappear).
3.  **Null Spike Detection**: Alerts if a run returns 0 items when it usually returns data.
4.  **AI Repair Engine**: When a selector breaks, it compares the old HTML snapshot with the new one and generates an LLM prompt to fix the CSS selector.
5.  **Dashboard**: View live status of all scrapers.

## Project Structure

```
├── api/                # Vercel entrypoint
├── backend/            # FastAPI Application
│   ├── app/            # App Logic (Models, DB, Analysis)
│   └── tests/          # Tests
├── frontend/           # Dashboard (HTML/JS)
├── sdk/                # Python Client SDK
├── demo/               # Demo Scraper Script
├── vercel.json         # Vercel Config
└── run_demo.sh         # Local Orchestrator
```
