import sys
import time
from playwright.sync_api import sync_playwright

def run_debug():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page.goto("https://adstransparency.google.com/?region=KR")
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        with open("atc_dom.html", "w", encoding="utf-8") as f:
            f.write(page.content())
            
        browser.close()

if __name__ == "__main__":
    run_debug()
