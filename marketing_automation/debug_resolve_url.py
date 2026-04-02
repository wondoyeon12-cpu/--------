import requests
from playwright.sync_api import sync_playwright

test_urls = [
    "https://thepine.co.kr/smart/KCMIFf250812/NP_GDN_05_og_2_2?utm_campaign=pine&utm_source=gdn&utm_medium=cpc&utm_content=sns&utm_term=NP_GDN_05_og_2_2",
    "https://thepine.co.kr/smart/YjEHNp250626/NP_GDN_05_og_2?utm_campaign=pine&utm_source=gdn&utm_medium=cpc&utm_content=sns&utm_term=NP_GDN_05_og_2"
]

def resolve_requests():
    print("--- Method 1: Requests (Mobile UA) ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://adstransparency.google.com/"
    }
    for url in test_urls:
        try:
            res = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
            print(f"Original: {url}")
            print(f"Final URL: {res.url}")
            print(f"Status: {res.status_code}")
            print(f"Content-Length: {len(res.text)}")
            if "healthystr" not in res.url:
                # Check if there is JS redirect in text
                if "window.location" in res.text or "http-equiv=\"refresh\"" in res.text:
                    print(f"  -> JS/Meta redirect found in body! (Lengths: {len(res.text)})")
        except Exception as e:
            print(f"Error: {e}")

def resolve_playwright():
    print("\n--- Method 2: Playwright (Mobile Simulation) ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # iPhone 13 Pro User Agent and Viewport
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True
        )
        page = context.new_page()
        
        for url in test_urls:
            try:
                print(f"Visiting: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(3000) # Wait for JS redirects
                print(f"Final URL: {page.url}")
            except Exception as e:
                print(f"Error: {e}")
                
        browser.close()

if __name__ == "__main__":
    resolve_requests()
    resolve_playwright()
