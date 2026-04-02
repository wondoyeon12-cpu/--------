import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def evaluate_article_quality(article):
    """
    OpenAI API를 사용하여 기사의 제목과 스니펫을 평가합니다.
    1점부터 10점까지의 점수를 반환하며, 7점 이상인 경우 유용한 기사로 판별합니다.
    """
    title = article.get("title", "")
    snippet = article.get("snippet", "")
    source = article.get("source", "")
    
    prompt = f"""
    당신은 1인 기업가와 예비 창업자를 위한 최고 수준의 프랜차이즈 비즈니스 분석가입니다. 
    다음 기사가 '프랜차이즈 동향파악이나 새로운 비즈니스 인사이트 도출'에 얼마나 유용한지 평가해주세요.
    점수는 1점부터 10점까지 부여하며, 숫자로만 응답해주세요.
    
    [평가 기준]
    - (9~10점) 프랜차이즈 트렌드 분석, 유망 업종 전망, 변화하는 소비 패턴에 대한 깊이 있는 통찰이 담긴 기사
    - (7~8점) 프랜차이즈 산업 관련 주요 정책 변화, 대형 브랜드의 유의미한 전략적 움직임
    - (4~6점) 단순 신규 브랜드 론칭, 매장 오픈 소식, 가벼운 단발성 이벤트 소식
    - (1~3점) 특정 브랜드의 단순 홍보성 기사(광고), 사건/사고, 가십거리

    기사 제목: {title}
    출처: {source}
    요약: {snippet}
    
    점수 (숫자만 입력):
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that evaluates news articles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.3
        )
        score_str = response.choices[0].message.content.strip()
        # 추출된 응답에서 숫자만 파싱 (예: "8", "8점" 대응)
        import re
        match = re.search(r'\d+', score_str)
        if match:
            score = int(match.group())
            return score
        else:
            return 0
    except Exception as e:
        print(f"Error evaluating article '{title}': {e}")
        return 0

def filter_articles(articles, threshold=7):
    """주어진 기사 목록을 평가하여 임계점 이상의 기사만 반환합니다."""
    filtered = []
    for article in articles:
        score = evaluate_article_quality(article)
        article['score'] = score # 점수 기록
        if score >= threshold:
            filtered.append(article)
        else:
            print(f"Filtered out: [{score}] {article.get('title')}")
    return filtered

def remove_semantic_duplicates(articles):
    """
    LLM을 활용하여 의미적으로 동일한(같은 행사/사건을 다룬) 기사들을 식별하고,
    중복되는 그룹 중 가장 점수가 높은 1개 기사만 남겨서 반환합니다.
    """
    if not articles or len(articles) <= 1:
        return articles
        
    print(f"🤖 OpenAI로 시맨틱 중복 검사 시작 (대상: {len(articles)}건)...")
    
    # 기사 목록을 LLM이 분석하기 좋은 텍스트 형식으로 변환
    article_texts = ""
    for idx, art in enumerate(articles):
        article_texts += f"[{idx}] 제목: {art.get('title')}\n    출처: {art.get('source')}\n\n"
        
    prompt = f"""
    당신은 꼼꼼하고 날카로운 분별력을 지닌 뉴스 편집장입니다.
    아래 뉴스 기사 목록(제목과 출처)을 읽고, 파생된 보도(동일한 행사, 동일한 사건 등 내용이 같은 기사)들을 하나로 묶어주세요.
    
    [핵심 지시사항]
    - 기사 제목과 출처만 보고도 내용이 중복되는 기사를 판단하여 같은 그룹으로 묶으세요.
    
    기사 목록:
    {article_texts}
    
    [응답 규칙]
    오직 유효한 JSON 배열(Array) 형태로만 응답해주세요. 아무런 부가 설명이나 Markdown 블록 코딩(```json)을 넣지 마세요.
    형식 예시: [[0, 2, 4], [1, 3]] (동일 사안인 기사 인덱스들의 배열. 중복이 없는 단독 기사의 인덱스는 출력하지 않아도 됩니다.)
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a JSON generating assistant. Only output raw JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        
        # Markdown 포맷 제거 (경우에 대비)
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        duplicate_groups = json.loads(content)
        
        # 삭제해야 할 인덱스 수집
        indices_to_remove = set()
        for group in duplicate_groups:
            if isinstance(group, list) and len(group) > 1:
                # 점수를 기준으로 정렬하여 가장 높은 점수의 인덱스 1개만 제외하고 나머지는 삭제 목록에 추가
                sorted_group = sorted(group, key=lambda idx: articles[idx].get('score', 0) if idx < len(articles) else 0, reverse=True)
                indices_to_remove.update(sorted_group[1:]) # 첫 번째(최고점) 제외하고 삭제 셋에 추가
                print(f"🔄 중복 기사 발견: 인덱스 {sorted_group} 중 최고점인 {sorted_group[0]}만 유지합니다.")
                
        # 최종 리스트 생성
        unique_articles = [art for idx, art in enumerate(articles) if idx not in indices_to_remove]
        print(f"✅ 중복 제거 완료: {len(articles)}건 -> {len(unique_articles)}건")
        return unique_articles

    except Exception as e:
        print(f"Error checking semantic duplicates (오류 발생으로 중복 검사 패스): {e}")
        return articles

if __name__ == "__main__":
    # Test
    sample_article = {
        "title": "올해 창업 트렌드는 '소자본 프랜차이즈'... 1인 기업가 주목",
        "snippet": "최근 경기 침체 속에서도 1인 주도로 창업할 수 있는 소자본 프랜차이즈가 각광받고 있습니다.",
        "source": "비즈니스 뉴스"
    }
    score = evaluate_article_quality(sample_article)
    print(f"Sample Score: {score}")

