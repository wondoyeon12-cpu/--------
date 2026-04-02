import sys
import time
from playwright.sync_api import sync_playwright

def run_debug(keyword):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page.goto("https://adstransparency.google.com/?region=KR")
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        try:
            # 1. Look for combobox
            box = page.get_by_role("combobox").first
            box.click(timeout=5000)
            time.sleep(1)
            box.fill(keyword)
            time.sleep(4)
            
            # 2. Look for the listbox options (autocomplete suggestions)
            options = page.get_by_role("option").all()
            print(f"Found {len(options)} options!")
            for i, opt in enumerate(options):
                if opt.is_visible():
                    text = opt.inner_text().strip()
                    print(f"Option {i}: {text}")
                    if i == 0:
                        opt.click()
                        break
        except Exception as e:
            print(f"Error: {e}")
            
        print("Wait for ads to load...")
        time.sleep(5)
        
        links = page.locator("a[href^='http']").all()
        for link in links:
            href = link.get_attribute("href")
            if "google.com" not in href and "youtube.com" not in href:
                print(f"Ad outbound Link: {href}")
            
        page.screenshot(path="atc_debug3.jpg")
        browser.close()

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
    run_debug("리피어라")
