import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse

# 보안 & 환경변수 세팅
load_dotenv(r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트\뉴스레터\.env")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def get_hidden_landing_urls_via_dorking(keyword):
    """
    네이버 파워링크 마스터 서버 직접 타격(Native Scraping) + 구글 모바일 광고 타격(SerpApi)
    [롤백 완료] 안정적인 링크 연결을 위해 초기 버전 로직으로 복구되었습니다.
    """
    extracted_data = []
    seen_urls = set()
    
    # ❌ 오픈마켓, 종합몰 등 가짜 랜딩(단순 판매처) 필터링
    def is_valid_url(combined_str):
        lower_str = combined_str.lower()
        blacklist = [
            "coupang", "gmarket", "auction", "11st", "ssg.com", 
            "smartstore.naver", "brand.naver", "naver.com", 
            "daum.net", "tistory.com", "blog", "news", 
            "youtube.com", "instagram.com", "facebook.com", "twitter.com",
            "/product/", "/category/", "/categories/", "/goods/", "/item/", "detail.html"
        ]
        
        for b in blacklist:
            if b in lower_str:
                return False
        return True

    # 1. 🇰🇷 네이버 파워링크 서버 심장부 다이렉트 타격
    naver_headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 14; SM-S928N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8'
    }
    
    power_suffixes = ["", "가격", "혜택", "이벤트", "할인", "효능", "부작용", "후기"]
    
    try:
        for suffix in power_suffixes:
            search_query = f"{keyword} {suffix}".strip()
            url = f"https://m.ad.search.naver.com/search.naver?where=m_ad&query={search_query}&pagingIndex=1"
            resp = requests.get(url, headers=naver_headers, timeout=5)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # [ROLLBACK] 초기 안정 버전 선택자로 복구
            ad_links = soup.select(".lnk_tit")
            for a_tag in ad_links:
                item = a_tag.find_parent("li")
                if not item: continue
                    
                desc_tag = item.select_one(".ad_dsc")
                disp_tag = item.select_one(".url")
                
                title = a_tag.text.strip()
                href = a_tag.get("href", "")
                desc = desc_tag.text.strip() if desc_tag else ""
                disp = disp_tag.text.strip() if disp_tag else ""
                
                # 프로토콜 보강
                final_url = href
                if final_url.startswith("//"):
                    final_url = "https:" + final_url
                
                combined_str = f"{title} {disp} {desc}"
                if is_valid_url(combined_str) and final_url:
                    if final_url not in seen_urls:
                        seen_urls.add(final_url)
                        extracted_data.append({
                            "url": final_url, 
                            "title": "[네이버 파워링크] " + title, 
                            "snippet": desc,
                            "source": "[Naver Native Server]"
                        })
    except Exception as e:
        print(f"🚨 Naver 에러 발생: {e}")

    # 2. 🇺🇸 구글 메인 모바일 광고 타격 (SerpApi 활용)
    if SERPAPI_API_KEY:
        google_params = {
            "engine": "google",
            "q": f"{keyword} (가격 OR 할인 OR 혜택 OR 이벤트 OR 효능 OR 후기)", 
            "api_key": SERPAPI_API_KEY,
            "hl": "ko",
            "gl": "kr",
            "device": "mobile"
        }
        
        try:
            resp = requests.get("https://serpapi.com/search", params=google_params, timeout=10)
            g_resp = resp.json()

            def add_unique_google_url(ad, source_name):
                link = ad.get("link", "")
                title = ad.get("title", "")
                snippet = ad.get("description", "") or ad.get("snippet", "")
                
                if link and is_valid_url(f"{title} {link} {snippet}"):
                    parsed = urlparse(link)
                    base_link = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    
                    if base_link not in seen_urls:
                        seen_urls.add(base_link)
                        extracted_data.append({
                            "url": link,
                            "title": f"[{source_name}] {title}",
                            "snippet": snippet,
                            "source": f"[Google {source_name.split()[0]}]"
                        })

            if "ads" in g_resp:
                for ad in g_resp["ads"]:
                    add_unique_google_url(ad, "모바일 스폰서광고")
            if "organic_results" in g_resp:
                for res in g_resp["organic_results"]:
                    add_unique_google_url(res, "자연 검색 (SEO)")
        except Exception as e:
            pass

    return extracted_data

if __name__ == "__main__":
    import sys
    test_keyword = sys.argv[1] if len(sys.argv) > 1 else "다이어트"
    results = get_hidden_landing_urls_via_dorking(test_keyword)
    for idx, res in enumerate(results, 1):
        print(f"{idx}. {res['title']} | {res['url']}")
