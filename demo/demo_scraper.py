import sys
import os
import requests
import time
from bs4 import BeautifulSoup

# Add the SDK to the path so we can import it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sdk.scraper_sre import ScraperObserver

API_URL = "http://localhost:8000/api/v1"

# 1. Register the Scraper
def register_scraper():
    print("Registering Scraper...")
    response = requests.post(f"{API_URL}/register", json={
        "name": "Pricing Monitor",
        "target_url": "https://example.com/products",
        "selectors": {"price": ".price"}
    })
    response.raise_for_status()
    scraper = response.json()
    print(f"Registered Scraper: {scraper['id']}")
    return scraper['id']

# Simulated HTML pages
HTML_V1 = """
<html>
    <body>
        <div class="product">
            <h1>Cool Widget</h1>
            <span class="price">$19.99</span>
        </div>
    </body>
</html>
"""

HTML_V2 = """
<html>
    <body>
        <div class="product">
            <h1>Cool Widget</h1>
            <span class="price-v2">$24.99</span>
        </div>
    </body>
</html>
"""

def run_scraper(scraper_id, html_content, version_name):
    print(f"\n--- Running Scraper ({version_name}) ---")
    observer = ScraperObserver(scraper_id, api_url=API_URL)

    with observer.monitor():
        # Simulate scraping logic
        soup = BeautifulSoup(html_content, 'html.parser')
        price_el = soup.select_one(".price")

        extracted_data = []
        if price_el:
            price = price_el.text
            print(f"Extracted Price: {price}")
            extracted_data.append({"price": price})
        else:
            print("Failed to find price element!")

        # Capture what we found
        observer.capture_data(extracted_data)
        observer.capture_snapshot(html_content)

if __name__ == "__main__":
    # Wait for server to be up
    print("Waiting for server...")
    time.sleep(2)

    try:
        scraper_id = register_scraper()

        # Run 1: Success
        run_scraper(scraper_id, HTML_V1, "V1 - Working")

        # Run 2: Failure (Drift)
        # We expect the observer to report 0 items extracted, which triggers NULL_SPIKE alert
        run_scraper(scraper_id, HTML_V2, "V2 - Broken")

        print("\nDemo completed. Check backend logs for alerts and repair suggestions.")

    except Exception as e:
        print(f"Demo failed: {e}")
