import sys
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

def get_google_atc_ads(keyword):
    urls = []
    seen = set()
    print(f"[{keyword}] 구글 광고 투명성 센터 우회 접속 및 딥 스캐닝 중...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 로봇 차단 우회를 위한 User-Agent 설정
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            # 1. ATC 페이지 접속
            page.goto("https://adstransparency.google.com/?region=KR", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(3)
            
            # 2. 모든 input 태그 검색 및 키워드 주입
            input_elements = page.locator("input").all()
            for inp in input_elements:
                if inp.is_visible():
                    try:
                        inp.fill(keyword)
                        time.sleep(1)
                        page.keyboard.press("Enter")
                        break
                    except Exception:
                        pass
            
            # 3. 드롭다운 리스트(material-list-item) 로드 대기 및 첫번째 항목 클릭
            time.sleep(3)
            items = page.locator("material-list-item").all()
            clicked = False
            for item in items:
                if item.is_visible():
                    item.click()
                    clicked = True
                    break
            
            if not clicked:
                page.keyboard.press("Enter")
                
            # 4. 광고 카드 그리드 로드 대기
            print("광고 카드 로딩 중...")
            time.sleep(8)
            
            # 5. 랜딩페이지 URL 싹쓸이 (a 태그 중 외부 도메인)
            links = page.locator("a[href^='http']").all()
            for link in links:
                href = link.get_attribute("href")
                if href and "google.com" not in href and "youtube.com" not in href:
                    parsed = urlparse(href)
                    netloc = parsed.netloc
                    # 구글 정적 자산 및 쓰레기 도메인 필터링
                    if netloc and "gstatic.com" not in netloc and "googlevideo.com" not in netloc:
                        # 긴 쿼리 스트링을 날려서 깨끗한 URL만 저장 (옵션)
                        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if clean_url not in seen:
                            seen.add(clean_url)
                            urls.append(clean_url)
                            
        except Exception as e:
            print(f"🚨 ATC 스크래핑 에러 (봇 차단 또는 셀렉터 변경): {e}")
            
        finally:
            browser.close()
            
    return urls

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "리피어라"
    res = get_google_atc_ads(kw)
    if not res:
        print("ATC에서 외부 광고 URL을 추출하지 못했습니다. (입력창 셀렉터 오류 또는 봇 차단 의심)")
    else:
        print("\n[발견된 찐 퍼포먼스 랜딩 URL 목록]")
        for idx, r in enumerate(res, 1):
            print(f"{idx}. {r}")
