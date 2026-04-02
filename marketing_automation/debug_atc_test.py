from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-web-security', '--disable-features=IsolateOrigins,site-per-process'])
    page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    print("Going to ATC...")
    page.goto("https://adstransparency.google.com/?region=KR", wait_until="domcontentloaded", timeout=40000)
    time.sleep(5)
    page.screenshot(path="atc_debug_test.jpg")
    print("Saved screenshot.")
    browser.close()
