import sys
import time
from playwright.sync_api import sync_playwright

def get_massive_naver_ads(keyword):
    urls = []
    seen = set()
    print(f"[{keyword}] 네이버 파워링크 마스터 서버 무제한 스캐닝 통신 중...")
    
    # ❌ 오픈마켓, 종합몰 등 가짜 랜딩(단순 판매처) 강력 필터링
    blacklist = ["coupang", "11st", "ssg", "danawa", "gmarket", "auction", "smartstore", "tmon", "wemakeprice", "lotteon", "interpark", "enuri", "nstore", "100ssd", "hnsmall", "cjonstyle", "gsshop", "hmall", "shinsegaetvshopping"]

    def is_valid(text):
        lower_text = text.lower()
        for b in blacklist:
            if b in lower_text:
                return False
        return True

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 네이버 봇 차단 우회용 PC 환경 헤더
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # 1~2 페이지(최대 50개 광고)를 싹 쓸어옵니다.
            for page_num in range(1, 3):
                target_url = f"https://ad.search.naver.com/search.naver?where=ad&query={keyword}&pagingIndex={page_num}"
                page.goto(target_url, timeout=15000)
                time.sleep(2)
                
                # 광고 리스트 아이템 파싱
                items = page.locator("li[class^='lst']").all()
                if not items:
                    break # 더 이상 광고가 없으면 종료
                    
                for item in items:
                    title_el = item.locator(".lnk_head")
                    disp_el = item.locator(".url")
                    desc_el = item.locator(".ad_dsc")
                    
                    if title_el.count() > 0:
                        title = title_el.first.inner_text().strip()
                        href = title_el.first.get_attribute("href")
                        disp = disp_el.first.inner_text().strip() if disp_el.count() > 0 else ""
                        desc = desc_el.first.inner_text().strip() if desc_el.count() > 0 else ""
                        
                        # 텍스트 삼중 교차 검증으로 숨은 쿠팡/지마켓 색출
                        combined = f"{title} {disp} {desc}"
                        
                        if is_valid(combined):
                            # 실제 노출되는 도메인을 최종 랜딩 URL로 확정 (트래킹 주소 제거)
                            clean_url = "http://" + disp.replace("/", "") if disp else href
                            
                            # 최종 URL에도 쿠팡 같은 글자가 섞여있지 않은지 4중 검수
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
