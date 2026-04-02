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
                    
            print("Typing complete. Getting full HTML...")
            html = page.content()
            with open("atc_autocomplete_dom.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Saved {len(html)} bytes to atc_autocomplete_dom.html")
            
            # Print any material-list-item or search-improvement-item or similar
            items = page.locator("material-list-item, .item, [role='option']").all()
            print(f"Found {len(items)} possible autocomplete items")
            for i, item in enumerate(items):
                try:
                    text = item.inner_text()
                    print(f"Item {i} text: {repr(text)}")
                except:
                    pass
            
        except Exception as e:
            print(f"Error: {e}")
            
        browser.close()

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
    run_debug("Samsung")
