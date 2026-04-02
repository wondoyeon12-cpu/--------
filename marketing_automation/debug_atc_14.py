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
            for i in range(15):
                page.keyboard.press("Tab")
                time.sleep(0.1)
                js = """() => {
                    let a = document.activeElement;
                    while(a && a.shadowRoot && a.shadowRoot.activeElement) a = a.shadowRoot.activeElement;
                    return a ? a.tagName : '';
                }"""
                if page.evaluate(js) == "INPUT":
                    page.keyboard.type(keyword, delay=200)
                    time.sleep(5)
                    break
                    
            items = page.locator("material-list-item, .item, [role='option']").all()
            for item in items:
                try:
                    if item.is_visible():
                        text = item.inner_text()
                        if "\n" in text and ("광고" in text or "인증" in text):
                            print(f"Clicking advertiser: {repr(text)}")
                            item.click()
                            break
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error: {e}")
            
        print("Wait for ads to load...")
        time.sleep(10)
        
        # Scroll down to load a few ads
        for _ in range(3):
            page.mouse.wheel(0, 1000)
            time.sleep(2)
            
        print("Scraping ad cards...")
        html = page.content()
        with open("atc_ad_grid_dom.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved {len(html)} bytes to atc_ad_grid_dom.html")
        
        # Also let's log all iframes
        frames = page.frames
        print(f"Total iframes: {len(frames)}")
        for i, frame in enumerate(frames):
            try:
                print(f"Frame {i} URL: {frame.url}")
                # Try to get links from inside frame
                a_tags = frame.locator("a[href^='http']").all()
                for a in a_tags:
                    print(f"   [Frame {i}] Link: {a.get_attribute('href')}")
            except Exception as e:
                pass

        browser.close()

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
    run_debug("Samsung")
