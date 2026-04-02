import sys
import json
import os
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

# 윈도우 콘솔에서 이모지 출력 시 발생하는 cp949 인코딩 에러 방지
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from scraper import fetch_google_news, extract_article_details
from llm_filter import filter_articles, remove_semantic_duplicates
from gsheet import get_subscribers
from emailer import create_email_html, send_newsletter

SENT_ARTICLES_FILE = "sent_articles.json"

def load_sent_articles():
    if os.path.exists(SENT_ARTICLES_FILE):
        with open(SENT_ARTICLES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_sent_articles(articles):
    with open(SENT_ARTICLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

def run_newsletter_job():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 코다리 뉴스레터 발송 작업 시작!")
    
    # 1. 키워드로 뉴스 스크래핑 (프랜차이즈 타겟팅)
    query = "프랜차이즈 뉴스"
    print(f"🔍 '{query}' 키워드로 뉴스 검색 중...")
    
    # 3차 고도화: 14일 치 데이터 수집
    articles = fetch_google_news(query, days=14)
    
    if not articles:
        print("❌ 검색된 기사가 없습니다.")
        return

    # 2. 중복 기사 제거 (이미 보낸 링크는 패스)
    sent_links = load_sent_articles()
    new_articles = [a for a in articles if a['link'] not in sent_links]
    print(f"📝 새로운 기사 {len(new_articles)}건 발견 (중복 {len(articles) - len(new_articles)}건 제외)")

    if not new_articles:
        print("🔔 새로 보낼 기사가 없습니다. 작업을 종료합니다.")
        return

    # 3. LLM으로 기사 품질 2차 평가 (7개 채우기 위해 전체 평가)
    print("🤖 OpenAI를 통한 기사 품질 평가 중...")
    # 7개의 기사를 확보하기 위해 평가 Pool 확대 (최대 30개)
    candidates = new_articles[:30] 
    # threshold 1로 설정하여 기사를 탈락시키지 않고 전부 점수만 매김
    filtered_articles = filter_articles(candidates, threshold=1)
    
    if not filtered_articles:
        print("🔔 평가할 유용한 기사가 없습니다. 작업을 종료합니다.")
        return
        
    # 점수가 높은 순으로 정렬
    filtered_articles.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # 시맨틱 중복 기사 제거 (가장 점수가 높은 1개만 남기고 필터링)
    unique_articles = remove_semantic_duplicates(filtered_articles)
    
    # 4. 선정된 기사에 썸네일 이미지 파싱 추가 및 빈 요약문(snippet) 보완
    print("📸 기사 썸네일 및 본문 추가 추출 중...")
    
    final_with_images = []
    # 먼저 상위 3개 자리(Main Report 1개, Deep Insights 2개)는 무조건 이미지가 있어야 함
    # 전체 필터링된 기사 목록에서 순차적으로 이미지가 있는 기사 3개를 먼저 확보합니다.
    image_required_count = 3
    
    # 중복 제거된 기사(7점 이상 포함) 전체에서 파싱을 시도
    for article in unique_articles:
        if len(final_with_images) >= image_required_count:
            break
            
        thumb, fallback_desc = extract_article_details(article['link'])
        article['thumbnail'] = thumb
        if not article.get('snippet') and fallback_desc:
            article['snippet'] = fallback_desc
            
        if thumb:  # 썸네일이 정상적으로 추출된 경우만 필수 슬롯에 추가
            final_with_images.append(article)
        time.sleep(1)
        
    # 만약 유효한 이미지를 가진 기사를 3개 채우지 못했다면 기존 풀에서 마저 채움 (에러 방지용)
    if len(final_with_images) < image_required_count:
        for article in filtered_articles:
            if len(final_with_images) >= image_required_count:
                break
            if article not in unique_articles:
                thumb, fallback_desc = extract_article_details(article['link'])
                article['thumbnail'] = thumb
                if not article.get('snippet') and fallback_desc:
                    article['snippet'] = fallback_desc
                if thumb:
                    final_with_images.append(article)
                time.sleep(1)

    # 나머지 4개 자리(Industry Pulse)는 이미지가 없어도 상관 없음
    non_image_articles = []
    for article in unique_articles:
        if len(final_with_images) + len(non_image_articles) >= 7:
            break
        if article not in final_with_images:
            thumb, fallback_desc = extract_article_details(article['link'])
            article['thumbnail'] = thumb
            if not article.get('snippet') and fallback_desc:
                article['snippet'] = fallback_desc
            non_image_articles.append(article)
            time.sleep(1)
            
    # 여전히 7개가 안 넘으면 전체 풀에서 당겨옴
    if len(final_with_images) + len(non_image_articles) < 7:
        for article in filtered_articles:
            if len(final_with_images) + len(non_image_articles) >= 7:
                break
            if article not in final_with_images and article not in non_image_articles:
                thumb, fallback_desc = extract_article_details(article['link'])
                article['thumbnail'] = thumb
                if not article.get('snippet') and fallback_desc:
                    article['snippet'] = fallback_desc
                non_image_articles.append(article)
                time.sleep(1)

    final_articles = final_with_images + non_image_articles

    # 5. 이메일 템플릿 렌더링
    print("✉️ 이메일 HTML 생성 중...")
    html_content = create_email_html(final_articles)
    
    # 6. 구독자 목록 조회 및 발송
    subscribers = ["wondoyeon12@gmail.com"] # get_subscribers()
    if not subscribers or (len(subscribers) == 1 and not subscribers[0]):
        print("❌ 구독자 목록을 불러오지 못했습니다. 발송 취소.")
        return
        
    print(f"📬 총 {len(subscribers)}명에게 메일 발송 시작...")
    today_str = datetime.now().strftime('%m월 %d일')
    subject = f"📰 [코다리 뉴스레터] {today_str} 돈이 되는 프랜차이즈/창업 핵심 뉴스"
    
    success = send_newsletter(subscribers, subject, html_content)
    
    # 7. 성공 시 중복 리스트 업데이트
    if success:
        for article in final_articles:
            sent_links.append(article['link'])
        save_sent_articles(sent_links)
        print("🏁 코다리 뉴스레터 발송 작업 성공적 완료! 충성!")
    else:
        print("❌ 뉴스레터 발송 실패!")


if __name__ == "__main__":
    # 테스트로 즉시 1회 실행
    run_newsletter_job()
    
    # 매일 아침 8시에 실행하도록 스케줄링하고 싶다면 아래 주석 해제
    # schedule.every().day.at("08:00").do(run_newsletter_job)
    # print("⏰ 매일 아침 08:00 예약 완료. 프로세스 대기 중...")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)

