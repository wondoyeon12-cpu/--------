import sys
import time
from playwright.sync_api import sync_playwright

def run_debug(keyword):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page.goto("https://adstransparency.google.com/?region=KR", wait_until="domcontentloaded")
        time.sleep(5)
        
        try:
            print("Locating exact input...")
            # ATC uses <search-input> and inside it an <input class="searchable-center-input">
            inp = page.locator("input.searchable-center-input, input[aria-label*='Search'], input[aria-label*='검색']").first
            inp.click(timeout=5000)
            time.sleep(1)
            inp.type(keyword, delay=200)
            
            print("Waiting for autocomplete overlay...")
            time.sleep(5)
            
            print("Pressing Down and Enter...")
            page.keyboard.press("ArrowDown")
            time.sleep(1)
            page.keyboard.press("Enter")
            
        except Exception as e:
            print(f"Error on input locator: {e}")
            
        print("Wait for ads to load...")
        time.sleep(10)
        
        links = page.locator("a[href^='http']").all()
        parsed = []
        for link in links:
            href = link.get_attribute("href")
            if "google.com" not in href and "youtube.com" not in href:
                parsed.append(href)
                
        print(f"Found {len(parsed)} non-google outbound links")
        for href in parsed:
            print(f"Ad outbound Link: {href}")
            
        page.screenshot(path="atc_debug8.jpg")
        browser.close()

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
    run_debug("리피어라")
