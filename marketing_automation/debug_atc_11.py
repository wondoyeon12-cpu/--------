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
            typed = False
            for inp in inputs:
                if inp.is_visible():
                    print("Found visible input, typing...")
                    inp.click(force=True)
                    time.sleep(1)
                    # Use keyboard type to trigger autocomplete
                    page.keyboard.type(keyword, delay=150)
                    typed = True
                    time.sleep(4) # Wait for autocomplete to appear
                    break
                    
            if typed:
                print("Checking material-list-item for Advertiser...")
                items = page.locator("material-list-item").all()
                print(f"Found {len(items)} items total on page.")
                clicked = False
                for i, item in enumerate(items):
                    if item.is_visible():
                        text = item.inner_text()
                        print(f"Item {i}: {text.replace(chr(10), ' ')}")
                        # We want the advertiser. Usually it says "광고주" or "Advertiser" in the subtitle.
                        if "광고주" in text or "Advertiser" in text or keyword in text:
                            # Skip the ones that are obviously just navigation links
                            if "FAQ" in text or "모든 주제" in text or "정치 광고" in text:
                                continue
                            print(f"-> CLICKING ITEM {i}!")
                            item.click()
                            clicked = True
                            break
                if not clicked:
                    print("No matching advertiser item found to click.")
                    
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
            
        page.screenshot(path="atc_debug11.jpg")
        browser.close()

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
    run_debug("리피어라")
