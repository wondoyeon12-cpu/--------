import sys
import time
from playwright.sync_api import sync_playwright

def run_debug(keyword):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page.goto("https://adstransparency.google.com/?region=KR")
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        inputs = page.locator("input").all()
        for i, inp in enumerate(inputs):
            if inp.is_visible():
                try:
                    inp.click()
                    time.sleep(1)
                    inp.type(keyword, delay=200) # Type slowly
                    time.sleep(3)
                    
                    # Keyboard navigation
                    page.keyboard.press("ArrowDown")
                    time.sleep(1)
                    page.keyboard.press("Enter")
                    break
                except Exception:
                    pass
                    
        print("Wait for ads to load...")
        time.sleep(10)
        
        # Ads
        links = page.locator("a[href^='http']").all()
        print(f"Found {len(links)} links")
        for link in links:
            href = link.get_attribute("href")
            # Filter standard google links
            if "google.com" not in href and "youtube.com" not in href:
                print(f"Ad outbound Link: {href}")
            
        page.screenshot(path="atc_debug2.jpg")
        browser.close()

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
    run_debug("리피어라")
