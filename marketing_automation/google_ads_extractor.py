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
    기존 1페이지만 긁던 한계를 돌파하여 최대 50개의 랜딩페이지를 싹쓸이합니다.
    """
    extracted_data = []
    seen_urls = set()
    
    # ❌ 오픈마켓, 종합몰 등 가짜 랜딩(단순 판매처) 필터링
    def is_valid_url(combined_str):
        """
        URL, 표시된 링크(displayed_link), 혹은 타이틀(title)을 모두 합쳐서
        강력한 블랙리스트 문자열이 하나라도 있으면 가차없이 폐기(False)
        """
        lower_str = combined_str.lower()
        
        # 대표적인 쓰레기/단순 마켓플레이스/포털/쇼핑몰 상세페이지 도메인 및 경로 모음
        blacklist = [
            "coupang", "gmarket", "auction", "11st", "ssg.com", 
            "smartstore.naver", "brand.naver", "naver.com", 
            "daum.net", "tistory.com", "blog", "news", 
            "youtube.com", "instagram.com", "facebook.com", "twitter.com",
            "/product/", "/category/", "/categories/", "/goods/", "/item/", "detail.html",
            "쇼핑몰", "패션", "남친룩", "코디", "데일리룩", "스타일", "스타일난다"
        ]
        
        for b in blacklist:
            if b in lower_str:
                return False
        return True

    # 1. 🇰🇷 네이버 파워링크 서버 심장부 다이렉트 타격 (모바일 환경 강제 적용)
    # 마케터 실무 탐색 패턴(혜택, 가격 등)을 덧붙여 다중 스캐닝 (무료이므로 무제한 타격 가능)
    naver_headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 14; SM-S928N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    # 찐 퍼포먼스 랜딩만 골라내는 '마법의 키워드' 조합
    power_suffixes = ["", "가격", "혜택", "이벤트", "할인", "효능", "부작용", "후기"]
    
    try:
        for suffix in power_suffixes:
            search_query = f"{keyword} {suffix}".strip()
            # 모바일 최적화 엔드포인트(m.ad.search.naver.com 및 where=m_ad) 타격
            url = f"https://m.ad.search.naver.com/search.naver?where=m_ad&query={search_query}&pagingIndex=1"
            resp = requests.get(url, headers=naver_headers, timeout=5)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # [UPDATE V2.2] 네이버 메인 파워링크 영역(#lst_site)만 정밀 타격
            ad_list = soup.select("#lst_site li")
            if not ad_list:
                # 구형 레이아웃 대응용 일반 선택자 보조
                ad_list = soup.select(".tit_wrap, .lnk_head, .ad_tit, .lnk_tit")
            
            if not ad_list:
                continue
                
            for item in ad_list:
                # [FIX V2.4] A 태그 정밀 포획 - 제목 상자가 div일 수 있으므로 내부의 진짜 'a' 태그를 확실히 찾습니다.
                a_tag = item if item.name == 'a' else item.select_one("a")
                
                if not a_tag:
                    # 상기 선택자로 못 찾은 경우 하위 모든 'a' 태그 중 첫 번째 시도
                    a_tag = item.find("a")
                
                if not a_tag or not a_tag.get("href"):
                    continue # 주소 태그가 없으면 광고 데이터가 아님
                    
                desc_tag = item.select_one(".ad_dsc")
                disp_tag = item.select_one(".url")
                
                title = a_tag.text.strip()
                href = a_tag.get("href", "")
                desc = desc_tag.text.strip() if desc_tag else ""
                disp = disp_tag.text.strip() if disp_tag else ""
                
                combined_str = f"{title} {disp} {desc}"
                
                # [NEW V2.2] 영역 기반으로 신뢰도를 높이되, 최소한의 연관성만 체크 (누락 방지)
                # '남친룩', '패션' 등은 is_valid_url(blacklist)에서 이미 걸러짐
                kw_low = keyword.lower().strip()
                title_low = title.lower()
                
                # 메인 영역 광고는 거의 100% 정답이므로 필터링을 대폭 완화
                # (제목에 한 글자라도 겹치거나, 그냥 메인 영역 광고면 일단 수집)
                is_related = kw_low in title_low or \
                             any(word in title_low for word in kw_low.split())
                if not is_related:
                    # 제목에 없더라도 설명이나 주소에 키워드가 있으면 통과
                    is_related = kw_low in combined_str.lower()

                if is_valid_url(combined_str) and is_related:
                    # [V2.3 EMERGENCY FIX] 
                    # 이전의 disp.replace("/", "") 로직은 URL을 파손시켜 Streamlit 내부 페이지로 튕기는 문제를 발생시켰음.
                    # 가장 확실한 연결을 위해 네이버 원본 광고 링크(href)를 우선 사용하고,
                    # href가 상대 경로(//)로 시작할 경우 프로토콜을 보강하여 외부 링크임을 명시함.
                    
                    final_link = href
                    if final_link.startswith("//"):
                        final_link = "https:" + final_link
                    elif not final_link.startswith("http"):
                        # 혹시 모를 프로토콜 누락 대비 (disp를 써야 하는 특수 상황 등)
                        final_link = "http://" + disp if disp else href

                    if is_valid_url(final_link) and final_link not in seen_urls:
                        seen_urls.add(final_link)
                        extracted_data.append({
                            "url": final_link, 
                            "title": "[네이버 V2.4] " + title, 
                            "snippet": desc,
                            "source": "[Naver Native Server]"
                        })
    except Exception as e:
        print(f"🚨 Naver 다이렉트 타격 중 에러 발생: {e}")

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
            g_resp = resp.json() # Renamed 'data' to 'g_resp' to match the provided snippet

            def add_unique_google_url(ad, source_name):
                # [FIX V2.4] Google 링크 필드 교차 검증 (link, url, snippet 내 주소 등)
                link = ad.get("link", ad.get("url", ad.get("canonical_link", "")))
                title = ad.get("title", "No Title")
                snippet = ad.get("description", ad.get("snippet", ""))
                
                if link and is_valid_url(f"{title} {link} {snippet}"):
                    # 쿼리스트링(utm 등)을 날려버리고 순수 도메인+경로만 남겨 동일 페이지 중복 방지
                    parsed = urlparse(link)
                    base_link = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    
                    if is_valid_url(base_link) and base_link not in seen_urls:
                        seen_urls.add(base_link)
                        extracted_data.append({
                            "url": link,
                            "title": f"[{source_name}] {title}",
                            "snippet": snippet,
                            "source": f"[Google {source_name.split()[0]}]"
                        })

            # 구글 모바일 스폰서드 광고 파싱
            if "ads" in g_resp:
                for ad in g_resp["ads"]:
                    add_unique_google_url(ad, "모바일 스폰서광고")
                    
            # 자연 검색 결과(SEO) 파싱 (정보성 포스팅은 최대한 배제)
            if "organic_results" in g_resp:
                for res in g_resp["organic_results"]:
                    add_unique_google_url(res, "자연 검색 (SEO)")
        except Exception as e:
            pass

    return extracted_data

if __name__ == "__main__":
    import sys
    test_keyword = sys.argv[1] if len(sys.argv) > 1 else "다이어트"
    print(f"\n[{test_keyword}] 유료 광고 랜딩 URL 폭격 스캐닝 시작...\n")
    
    results = get_hidden_landing_urls_via_dorking(test_keyword)
    
    if not results:
        print("데이터를 찾지 못했습니다.")
    else:
        for idx, res in enumerate(results, 1):
            print(f"{idx}. {res['title']} | {res['url']}")
