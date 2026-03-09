# Scraper SRE Platform

![Python Badge](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![FastAPI Badge](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)
![JavaScript Badge](https://img.shields.io/badge/JavaScript-ES6%2B-F7DF1E?logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green.svg)

An SRE (Site Reliability Engineering) observability layer and self-healing engine for web scraping operations. It monitors scraper success rates, detects schema drift and null spikes, and leverages AI to generate repair suggestions for broken CSS selectors.

---

## 📸 Demo / Screenshot

> *(Add a screenshot or GIF of the Scraper SRE Dashboard showing scraper metrics, runs, and alerts here)*

---

## ✨ Features

- **📊 Scraper Observability**: Track every execution of your scrapers, logging success/failure states, durations, and extraction counts.
- **🚨 Schema Drift Detection**: Receive immediate alerts when the targeted website's data structure changes or keys disappear.
- **📉 Null Spike Alerts**: Detect silent failures where a scraper successfully runs but returns 0 items unexpectedly.
- **🤖 AI-Powered Repair Engine**: When a selector breaks, the platform compares pre-failure and post-failure HTML snapshots to automatically suggest an updated CSS selector.
- **💻 Universal Dashboard**: Single-page application (SPA) dashboard to visualize the real-time status of all active scrapers and alerts.
- **🔌 Python SDK**: Drop-in Python client (`ScraperObserver`) to instrument your existing scraping scripts with minimal overhead.

---

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, Motor (Async MongoDB), BeautifulSoup4, LXML
- **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS (via CDN)
- **Database**: MongoDB Atlas (with local in-memory fallback for testing)
- **Deployment**: Vercel (Backend API) / GitHub Pages (Frontend UI)

---

## 📂 Project Structure

```text
├── api/                   # Vercel entrypoint for serverless deployment
│   └── index.py
├── backend/               # FastAPI Application
│   ├── app/               # Core Application Logic
│   │   ├── analyzer.py    # Drift and failure detection logic
│   │   ├── database.py    # MongoDB & Mock in-memory connections
│   │   ├── main.py        # FastAPI routes and server init
│   │   ├── models.py      # Pydantic data models
│   │   └── repair.py      # AI repair prompt generation
│   └── tests/             # Backend test suite
├── demo/                  # Example scraper implementation
│   └── demo_scraper.py    # Script demonstrating the SDK in action
├── frontend/              # Static Dashboard SPA
│   ├── index.html
│   ├── script.js
│   └── style.css
├── sdk/                   # Python Client SDK
│   └── scraper_sre/       # Core SDK package
│       └── client.py      # ScraperObserver context manager
├── README.md              # Project documentation
├── requirements.txt       # Python dependencies
├── run_demo.sh            # Local orchestrator for backend, frontend, and demo
└── vercel.json            # Vercel serverless configuration
```

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: v3.8 or higher
- **Node.js & npm**: Optional, required only if using the Vercel CLI (`npm i -g vercel`)
- **MongoDB Atlas**: Optional, needed for persistence. The app defaults to an in-memory mock database if no URL is provided.

---

## 🚀 Installation & Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/scraper-sre-platform.git
   cd scraper-sre-platform
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Full Stack Demo**
   The project includes a convenient bash script that boots the backend, serves the frontend, and runs a demo scraper.
   ```bash
   ./run_demo.sh
   ```
   *This starts the API on `http://localhost:8000` and the UI on `http://localhost:8080`.*

### Manual Start

To start the components individually:

**Backend:**
```bash
uvicorn backend.app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
python3 -m http.server 8080
```

---

## 💻 Usage

Instrument your existing Python scrapers using the provided `sdk`.

First, register your scraper to get an ID. Then, wrap your scraping logic in the `ScraperObserver.monitor()` context manager.

```python
import requests
from bs4 import BeautifulSoup
from sdk.scraper_sre import ScraperObserver

API_URL = "http://localhost:8000/api/v1"

# 1. Register the Scraper to get a unique scraper_id
response = requests.post(f"{API_URL}/register", json={
    "name": "E-commerce Monitor",
    "target_url": "https://example-store.com/products",
    "selectors": {"price": ".product-price"}
})
scraper_id = response.json()['id']

# 2. Instrument your scraping logic
observer = ScraperObserver(scraper_id, api_url=API_URL)

html_content = "<html><body><div class='product-price'>$29.99</div></body></html>"

with observer.monitor():
    soup = BeautifulSoup(html_content, 'html.parser')
    price_element = soup.select_one(".product-price")

    extracted_data = []
    if price_element:
        extracted_data.append({"price": price_element.text})

    # Capture the snapshot and data for the SRE platform to analyze
    observer.capture_snapshot(html_content)
    observer.capture_data(extracted_data)
```

---

## 🔐 Environment Variables

| Variable | Description | Default | Example |
| :--- | :--- | :--- | :--- |
| `MONGODB_URL` | The MongoDB connection string (SRV format). If unset, the app uses an in-memory mock database. | `mock://` | `mongodb+srv://user:pass@cluster.mongodb.net/test` |

---

## 🌐 API Reference

The backend exposes a RESTful JSON API.

### `POST /api/v1/register`
Registers a new scraper configuration.
- **Payload:** `{"name": "string", "target_url": "string", "selectors": {"key": "selector"}}`
- **Returns:** Scraper object with a generated `id`.

### `POST /api/v1/ingest`
Ingests metrics for a single scraper run. Triggers asynchronous drift analysis.
- **Payload:** `{"scraper_id": "string", "status": "SUCCESS|FAILURE", "duration_ms": float, "items_extracted": int, ...}`
- **Returns:** `{"run_id": "string", "status": "processing"}`

### `GET /api/v1/scrapers`
Retrieves a list of all registered scrapers.
- **Returns:** Array of Scraper objects.

### `GET /api/v1/scrapers/{scraper_id}/alerts`
Retrieves all alerts generated for a specific scraper.
- **Returns:** Array of Alert objects.

---

## 🏗️ Configuration

### Deployment via Vercel

The backend is pre-configured for Vercel Serverless Functions via the included `vercel.json` and `api/index.py` files.

1. Install the Vercel CLI: `npm i -g vercel`
2. Authenticate and deploy:
   ```bash
   vercel
   ```
3. Set your `MONGODB_URL` inside the Vercel dashboard environment variables for persistence.

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve the AI repair engine, add new drift detection patterns, or enhance the UI:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- Built with [FastAPI](https://fastapi.tiangolo.com/) for high-performance async endpoints.
- Uses [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing and DOM extraction.
- Styled with [Tailwind CSS](https://tailwindcss.com/).
