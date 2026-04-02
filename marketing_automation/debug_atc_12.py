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
            print("Tab probing...")
            found = False
            for i in range(15):
                page.keyboard.press("Tab")
                time.sleep(0.5)
                
                # Check active element using JS Shadow DOM piercer
                js = """
                () => {
                    let active = document.activeElement;
                    while (active && active.shadowRoot && active.shadowRoot.activeElement) {
                        active = active.shadowRoot.activeElement;
                    }
                    if(!active) return '';
                    let p = active.getAttribute('placeholder') || '';
                    let a = active.getAttribute('aria-label') || '';
                    return p + " | " + a + " | " + active.tagName;
                }
                """
                active_info = page.evaluate(js)
                print(f"Tab {i}: Active Element Info = {active_info}")
                
                if "Search" in active_info or "검색" in active_info or "광고주" in active_info or active_info.endswith("| INPUT"):
                    print("Found search box!")
                    page.keyboard.type(keyword, delay=150)
                    found = True
                    time.sleep(4)
                    break
                    
            if found:
                print("Checking autocomplete items...")
                items = page.locator("material-list-item").all()
                clicked = False
                for idx, item in enumerate(items):
                    if item.is_visible():
                        text = item.inner_text()
                        print(f"Item {idx}: {text.replace(chr(10), ' ')}")
                        if "광고주" in text or "Advertiser" in text or keyword in text:
                            if "FAQ" in text or "모든 주제" in text:
                                continue
                            print(f"-> CLICKING ITEM {idx}!")
                            item.click()
                            clicked = True
                            break
                if not clicked:
                    print("No matching advertiser item.")
                    
        except Exception as e:
            print(f"Error on probing: {e}")
            
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
            
        page.screenshot(path="atc_debug12.jpg")
        browser.close()

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
    run_debug("리피어라")
