import sys
import time
from playwright.sync_api import sync_playwright

def test_google_atc(keyword):
    print(f"[{keyword}] 구글 광고 투명성 센터 스캐닝 테스트...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ko-KR",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # 구글 ATC는 URL에 쿼리를 넣어도 바로 검색 결과로 안 갈 수도 있으므로 메인 접속 후 키입력 시도
            url = f"https://adstransparency.google.com/?region=KR"
            page.goto(url, timeout=30000)
            page.wait_for_timeout(3000)
            
            # 입력창 클릭 및 검색어 입력 후 엔터 (Shadow DOM 내부라도 get_by_role 등 활용)
            print("검색창 탐색 중...")
            
            # 구글 ATC 검색창은 보통 input 태그
            search_box = page.locator("input").first
            search_box.fill(keyword)
            page.wait_for_timeout(2000)
            page.keyboard.press("Enter")
            
            print("결과 대기 중...")
            page.wait_for_timeout(5000)
            
            # 디버깅용 스크린샷 캡처
            page.screenshot(path="atc_test.png", full_page=True)
            print("스크린샷 저장 완료 (atc_test.png)")
            
            # 전체 텍스트 덤프로 뭐가 뜨는지 확인
            texts = page.locator("body").inner_text()
            print(f"--- 텍스트 덤프 (앞부분 500자) ---\n{texts[:500]}")
            
        except Exception as e:
            print(f"에러 발생: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "리피어라"
    test_google_atc(kw)
