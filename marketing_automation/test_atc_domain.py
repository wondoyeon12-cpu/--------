import sys
from playwright.sync_api import sync_playwright

def test_atc_keyword_search(keyword):
    print(f"[{keyword}] 구글 ATC 전체 키워드 검색 통합 테스트...")
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(locale="ko-KR", viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        try:
            url = f"https://adstransparency.google.com/?region=KR"
            page.goto(url, timeout=30000)
            page.wait_for_timeout(3000)
            
            search_box = page.locator("input").first
            search_box.fill(keyword)
            # 드롭다운 애니메이션 대기
            page.wait_for_timeout(2000)
            
            print("드롭다운 하단의 '검색 결과 더보기' 클릭 시도...")
            page.screenshot(path="atc_before_click.png", full_page=True)
            
            # 검색 결과 더보기 텍스트를 찾아 강제 클릭
            more_results_btn = page.get_by_text("검색 결과 더보기")
            if more_results_btn.count() > 0:
                more_results_btn.first.click(force=True)
                print("클릭 성공! 광고 카드 렌더링 대기 중...")
                page.wait_for_timeout(5000)
                
                # 결과 페이지 전체 스크린샷
                page.screenshot(path="atc_after_click.png", full_page=True)
                print("최종 결과 스크린샷 저장 완료 (atc_after_click.png)")
                
                # 광고 카드(material-card 또는 <a> 태그 하위의 광고 요소들) 개수 파악
                ads = page.locator("creative-preview")
                print(f"화면에 렌더링된 광고(creative-preview) 개수: {ads.count()}")
            else:
                print("'검색 결과 더보기' 버튼을 찾을 수 없습니다.")
                
        except Exception as e:
            print(f"에러 발생: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "리피어라"
    test_atc_keyword_search(kw)
