import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse

# 보안 & 환경변수 세팅 - 현재 폴더와 상위 폴더까지 탐색하여 .env 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트\뉴스레터\.env") # 하위 호환 유지
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def get_hidden_landing_urls_via_dorking(keyword):
    """
    네이버 파워링크 마스터 서버 직접 타격(Native Scraping) + 구글 모바일 광고 타격(SerpApi)
    [고도화] 한 쪽 엔진이 실패해도 다른 쪽은 반드시 가동되도록 독립성을 강화했습니다.
    """
    extracted_data = []
    seen_urls = set()
    
    # ❌ 오픈마켓, 종합몰 등 가짜 랜딩(단순 판매처) 필터링 (필터 조건 완화하여 유실 방지)
    def is_valid_url(combined_str):
        lower_str = combined_str.lower()
        blacklist = [
            "coupang", "gmarket", "auction", "11st", "ssg.com", 
            "smartstore.naver", "brand.naver",
            "daum.net", "tistory.com", "news", 
            "youtube.com", "instagram.com", "facebook.com", "twitter.com"
        ]
        
        for b in blacklist:
            if b in lower_str:
                return False
        return True

    # 1. 🇰🇷 네이버 다이렉트 타격
    try:
        import importlib
        import naver_ad_spider
        importlib.reload(naver_ad_spider)
        naver_results = naver_ad_spider.get_massive_naver_ads(keyword)
        if naver_results:
            for item in naver_results:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    extracted_data.append(item)
        else:
            print("  [Naver] 수집된 결과가 없습니다.")
    except Exception as e:
        print(f"🚨 Naver 다이렉트 타격 중 에러 발생 (독립성 유지됨): {e}")

    # 2. 🇺🇸 구글 메인 모바일 광고 타격 (SerpApi 활용)
    if SERPAPI_API_KEY:
        def fetch_google_results(q):
            google_params = {
                "engine": "google",
                "q": q, 
                "api_key": SERPAPI_API_KEY,
                "hl": "ko",
                "gl": "kr",
                "device": "mobile"
            }
            try:
                resp = requests.get("https://serpapi.com/search", params=google_params, timeout=10)
                return resp.json()
            except:
                return {}

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

        # --- 1차 시도: 정밀 검색 (Dorking) ---
        q_precise = f"{keyword} (가격 OR 할인 OR 혜택 OR 이벤트 OR 효능 OR 후기)"
        g_resp = fetch_google_results(q_precise)
        
        has_results = False
        if "ads" in g_resp:
            for ad in g_resp["ads"]:
                add_unique_google_url(ad, "모바일 스폰서광고")
                has_results = True
        if "organic_results" in g_resp:
            for res in g_resp["organic_results"]:
                add_unique_google_url(res, "자연 검색 (SEO)")
                has_results = True

        # --- 2차 시도: 결과가 없을 경우 키워드만으로 일반 검색 ---
        if not has_results:
            print(f"  [Google] 정밀 검색 결과 없음 -> 일반 검색으로 재시도 중: {keyword}")
            g_resp = fetch_google_results(keyword)
            if "ads" in g_resp:
                for ad in g_resp["ads"]:
                    add_unique_google_url(ad, "모바일 스폰서광고")
            if "organic_results" in g_resp:
                for res in g_resp["organic_results"]:
                    add_unique_google_url(res, "자연 검색 (SEO)")

    else:
        print("🚨 SERPAPI_API_KEY가 설정되지 않아 구글 탐지를 생략합니다.")

    return extracted_data

if __name__ == "__main__":
    import sys
    test_keyword = sys.argv[1] if len(sys.argv) > 1 else "다이어트"
    results = get_hidden_landing_urls_via_dorking(test_keyword)
    for idx, res in enumerate(results, 1):
        print(f"{idx}. {res['title']} | {res['url']}")
