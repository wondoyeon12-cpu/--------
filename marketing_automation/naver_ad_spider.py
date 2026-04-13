import sys
import time
import asyncio
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def get_massive_naver_ads(keyword):
    urls = []
    seen = set()
    print(f"[{keyword}] 네이버 파워링크 마스터 서버 무제한 스캐닝 통신 중...")
    
    # ❌ 오픈마켓, 종합몰 등 가짜 랜딩(단순 판매처) 필터링
    # detail.html 등 실제 랜딩페이지 주소는 제외하지 않도록 조정
    blacklist = ["coupang", "11st", "ssg", "danawa", "gmarket", "auction", "smartstore", "tmon", "wemakeprice", "lotteon", "interpark", "enuri", "nstore", "100ssd", "hnsmall", "cjonstyle", "gsshop", "hmall", "shinsegaetvshopping"]

    def is_valid(text):
        lower_text = text.lower()
        for b in blacklist:
            if b in lower_text:
                return False
        return True

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            for page_num in range(1, 3):
                target_url = f"https://ad.search.naver.com/search.naver?where=ad&query={keyword}&pagingIndex={page_num}"
                page.goto(target_url, timeout=15000)
                page.wait_for_timeout(2000)
                
                # [수정] 클래스명 lst가 사라졌으므로, 구조적으로 li를 탐색합니다.
                items = page.locator("#container li").all()
                if not items:
                    break
                    
                for item in items:
                    # [수정] 태그 형태가 바뀐 선택자들을 업데이트합니다.
                    title_el = item.locator("a.tit_wrap")
                    disp_el = item.locator("a.url")
                    desc_el = item.locator("a.link_desc")
                    
                    if title_el.count() > 0:
                        title = title_el.first.inner_text().strip()
                        href = title_el.first.get_attribute("href")
                        disp = disp_el.first.inner_text().strip() if disp_el.count() > 0 else ""
                        desc = desc_el.first.inner_text().strip() if desc_el.count() > 0 else ""
                        
                        combined = f"{title} {disp} {desc}"
                        
                        if is_valid(combined):
                            # [수정] disp.replace("/", "") 오류 제거: 슬래시가 포함된 유효한 URL도 그대로 유지
                            clean_url = "http://" + disp.strip() if disp else href
                            
                            if is_valid(clean_url):
                                if clean_url not in seen:
                                    seen.add(clean_url)
                                    urls.append({
                                        "url": clean_url,
                                        "title": f"[네이버 최상위 파워링크] {title}",
                                        "snippet": desc,
                                        "source": "[Naver Massive Spider]"
                                    })
        except Exception as e:
            print(f"에러 발생: {e}")
        finally:
            browser.close()
            
    return urls

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "다이어트"
    res = get_massive_naver_ads(kw)
    print(f"\n최종 타격: {len(res)}개 랜딩 확보 성공!")
    for idx, r in enumerate(res, 1):
        print(f"{idx}. {r['url']}")
