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
        
        js_code = """
        () => {
            const getShadowInputs = (root) => {
                let inputs = [];
                const descendants = root.querySelectorAll('*');
                for (let el of descendants) {
                    if (el.tagName === 'INPUT') inputs.push(el);
                    if (el.shadowRoot) inputs.push(...getShadowInputs(el.shadowRoot));
                }
                return inputs;
            }
            const inputs = getShadowInputs(document);
            if(inputs.length > 0) {
                // Return placeholder or aria-label of all inputs
                return inputs.map(i => i.getAttribute('placeholder') || i.getAttribute('aria-label') || 'unknown');
            }
            return [];
        }
        """
        
        input_attributes = page.evaluate(js_code)
        print(f"Shadow DOM Inputs found: {input_attributes}")
        
        # Focus and type into the first one that seems like a search box
        focus_js = """
        () => {
            const getShadowInputs = (root) => {
                let inputs = [];
                const descendants = root.querySelectorAll('*');
                for (let el of descendants) {
                    if (el.tagName === 'INPUT') inputs.push(el);
                    if (el.shadowRoot) inputs.push(...getShadowInputs(el.shadowRoot));
                }
                return inputs;
            }
            const inputs = getShadowInputs(document);
            // find the one that has search or 광고주
            for(let i of inputs) {
                let p = i.getAttribute('placeholder') || '';
                let a = i.getAttribute('aria-label') || '';
                if(p.includes('검색') || p.includes('Search') || a.includes('Search') || a.includes('검색')) {
                    i.focus();
                    return true;
                }
            }
            if(inputs.length > 0) {
                inputs[0].focus();
                return true;
            }
            return false;
        }
        """
        
        focused = page.evaluate(focus_js)
        print(f"Was search input focused? {focused}")
        
        if focused:
            time.sleep(1)
            page.keyboard.type(keyword, delay=150)
            print("Typed keyword")
            time.sleep(3)
            
            # Now we must select the autocomplete item.
            # In ATC, an autocomplete overlay appears. We can use keyboard.
            page.keyboard.press("ArrowDown")
            time.sleep(1)
            page.keyboard.press("Enter")
            print("Pressed Down and Enter")
            
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
            
        page.screenshot(path="atc_debug5.jpg")
        browser.close()

if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
    run_debug("리피어라")
