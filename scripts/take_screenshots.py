import time
from playwright.sync_api import sync_playwright
import os

PAGES = {
    "overview": "http://localhost:8501",
    "news_explorer": "http://localhost:8501/News_Explorer",
    "analytics": "http://localhost:8501/Analytics",
    "source_analytics": "http://localhost:8501/Source_Analytics",
    "insights": "http://localhost:8501/Insights"
}

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        
        # Make sure the directory exists
        os.makedirs("docs/images", exist_ok=True)
        
        for name, url in PAGES.items():
            print(f"Capturing {name}...")
            # Wait until there are no active network requests (Streamlit takes a bit to render)
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                # Wait an extra 2 seconds for Plotly charts to render completely
                page.wait_for_timeout(2500)
                page.screenshot(path=f"docs/images/{name}.png")
            except Exception as e:
                print(f"Error capturing {name}: {e}")
                
        browser.close()

if __name__ == "__main__":
    take_screenshots()
