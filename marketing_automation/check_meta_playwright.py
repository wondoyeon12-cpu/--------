import sys
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

def test_meta_ads(keyword):
    print(f"[{keyword}] Meta Ads Library (Playwright) 스캐닝 시작...")
    urls = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ko-KR",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=KR&q={keyword}&search_type=keyword_unordered&media_type=all"
            page.goto(url, timeout=30000)
            
            # 페이지 초기 로딩 대기
            print("페이지 로딩 중...")
            page.wait_for_timeout(5000)
            
            # 스크롤을 여러 번 내려서 다중 광고 로드 (Lazy loading)
            for _ in range(3):
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(2000)
            
            # 디버깅용 스크린샷 캡처
            page.screenshot(path="meta_test.png", full_page=True)
            print("스크린샷 저장 완료 (meta_test.png)")
            
            # 광고 컨테이너나 모든 외부 링크 a 태그 찾기
            links = page.locator("a[href]").all()
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href:
                        if "/l.php?u=" in href:
                            from urllib.parse import parse_qs
                            qs = parse_qs(urlparse(href).query)
                            if "u" in qs:
                                real_url = qs["u"][0]
                                if "facebook.com" not in real_url:
                                    urls.add(real_url)
                        elif href.startswith("http") and "facebook.com" not in href and "fb.com" not in href:
                            urls.add(href)
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"에러: {e}")
        finally:
            browser.close()
            
    print(f"\n[발견된 외부 랜딩 URL: {len(urls)}개]")
    for i, u in enumerate(list(urls)[:20], 1):
        print(f"{i}. {u}")

if __name__ == "__main__":
    test_keyword = sys.argv[1] if len(sys.argv) > 1 else "다이어트"
    test_meta_ads(test_keyword)
