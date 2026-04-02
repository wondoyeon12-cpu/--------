import os
import json
import requests
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def fetch_google_news(query, days=14):
    """SerpAPI를 통해 최신 뉴스 검색 (최대 10~20개 조회)"""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_news",
        "q": query,
        "gl": "kr",
        "hl": "ko",
        "tbs": f"qdr:d{days}", # x일 이내
        "api_key": SERPAPI_API_KEY
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    articles = []
    now_utc = datetime.now(timezone.utc).date()
    
    for result in data.get("news_results", []):
        date_str = result.get("date", "")
        if not date_str:
            continue
            
        keeper = False
        date_str_lower = date_str.lower()
        
        # 1. Relative string check like 'ago', 'mins', 'hours', '전'
        if any(x in date_str_lower for x in ['ago', 'min', 'hour', '전']):
            if 'day' in date_str_lower or '일 전' in date_str_lower:
                num_match = re.search(r'(\d+)', date_str)
                if num_match and int(num_match.group(1)) <= days:
                    keeper = True
            else:
                keeper = True # hours or mins ago
        else:
            # 2. Parse absolute date MM/DD/YYYY
            match = re.search(r'(\d{2}/\d{2}/\d{4})', date_str)
            if match:
                try:
                    article_date = datetime.strptime(match.group(1), '%m/%d/%Y').date()
                    if (now_utc - article_date).days <= days:
                        keeper = True
                except ValueError:
                    pass
        
        if keeper:
            articles.append({
                "title": result.get("title"),
                "link": result.get("link"),
                "source": result.get("source", {}).get("name"),
                "date": date_str,
                "snippet": result.get("snippet", "")
            })
            
    return articles

def extract_article_details(url):
    """뉴스 원문 URL에 접속해 이미지(og:image)와 본문 일부(og:description 또는 첫 번째 <p>) 파싱"""
    thumbnail = ""
    description = ""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # og:image 추출
        og_img = soup.find("meta", property="og:image")
        thumbnail = og_img["content"] if og_img else ""
        
        # og:description 추출
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            description = og_desc["content"].strip()
        else:
            # og:description이 없으면 첫 번째 유의미한 <p> 태그 내용 추출
            paragraphs = soup.find_all("p")
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 40: # 적어도 40자는 넘어야 본문으로 간주
                    description = text
                    break
                    
        return thumbnail, description
    except Exception as e:
        print(f"Error extracting details from {url}: {e}")
        return thumbnail, description

if __name__ == "__main__":
    articles = fetch_google_news("프랜차이즈")
    print(f"Found {len(articles)} articles.")
    for idx, article in enumerate(articles[:2]):
        print(f"\n[{idx+1}] {article['title']}")
        print(article['link'])
        thumb, desc = extract_article_details(article['link'])
        print(f"Thumbnail: {thumb}")
        print(f"Description: {desc}")
