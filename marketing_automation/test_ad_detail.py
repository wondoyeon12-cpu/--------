import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # 특정 광고 상세 페이지로 접속 (예: 파인네스트 광고)
        url = "https://adstransparency.google.com/advertiser/1577922613/creative/778855606737?region=KR"
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="domcontentloaded")
        
        # 5초 대기 후 프레임 스캔 (네트워크 안정화)
        await page.wait_for_timeout(5000)
        
        for i, frame in enumerate(page.frames):
            print(f"--- Frame {i}: {frame.url}")
            try:
                anchors = await frame.locator("a").all()
                for a in anchors:
                    href = await a.get_attribute("href")
                    if href:
                        print(f"  [a href] {href[:100]}")
            except Exception as e:
                print(f"  Error reading frame: {e}")
                
        # HTML 덤프
        with open("atc_ad_detail_dump.html", "w", encoding="utf-8") as f:
            f.write(await page.content())
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
