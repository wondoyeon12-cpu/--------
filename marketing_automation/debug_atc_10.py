import sys
import time
from playwright.sync_api import sync_playwright

def run_debug(keyword):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page.goto("https://adstransparency.google.com/?region=KR", wait_until="domcontentloaded")
        time.sleep(5)
        
        try:
            print("Finding visible inputs...")
            inputs = page.locator("input").all()
            for inp in inputs:
                if inp.is_visible():
                    print("Found visible input, typing...")
                    inp.click(force=True)
                    time.sleep(1)
                    
                    # Some inputs clear when typed. Let's send characters one by one.
                    inp.type(keyword, delay=200)
                    time.sleep(3)
                    
                    print("Pressing Down ...")
                    page.keyboard.press("ArrowDown")
                    time.sleep(1)
                    print("Pressing Enter ...")
                    page.keyboard.press("Enter")
                    break
            
        except Exception as e:
            print(f"Error on search-input: {e}")
            
        print("Wait for ads to load...")
        time.sleep(8)
        
        links = page.locator("a[href^='http']").all()
        parsed = []
        for link in links:
            href = link.get_attribute("href")
            if "google.com" not in href and "youtube.com" not in href:
                parsed.append(href)
                
        print(f"Found {len(parsed)} non-google outbound links")
        for href in parsed:
            print(f"Ad outbound Link: {href}")
            
        page.screenshot(path="atc_debug10.jpg")
        browser.close()

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
    run_debug("리피어라")
