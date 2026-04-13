import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def get_ai_answer(question_text, recent_history):
    """
    슬랙에서 질문이 들어왔을 때, 최근 대화 내역을 바탕으로 답변을 생성합니다.
    - question_text: 사용자의 질문 내용
    - recent_history: DB에서 가져온 최근 대화 객체 리스트 
                      [(user_id, text, timestamp), ...]
    """
    if not client:
        return "OpenAI API 키가 설정되지 않았습니다."

    history_str = ""
    for user_id, text, timestamp in recent_history:
        history_str += f"[{timestamp}] User {user_id}: {text}\n"

    system_prompt = (
        "당신은 플러스위시드의 장 대표님을 보좌하는 든든하고 유쾌한 AI 비서실장 '위시드(WECYD)'입니다.\n"
        "다음은 이 슬랙 채널의 최근 대화 내역입니다.\n"
        "이 대화 내역을 바탕으로 대표님의 질문에 명확하고 친절하게 답변해주세요.\n"
        "답변 시작은 반드시 '충성! 위시드 비서 실장입니다!' 로 시작하고, "
        "마무리는 '저 위시드는 언제든 대표님의 얘기에 귀기울일 준비가 되어 있습니다! 언제든 불러주십쇼 😎' 라고 끝내주세요.\n\n"
        f"--- 최근 대화 내역 ---\n{history_str}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question_text}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 응답 생성 중 오류가 발생했습니다: {e}"

def generate_daily_summary(daily_messages):
    """
    하루 동안의 슬랙 메시지 전체를 분석하여 보고서 형태의 마크다운 요약을 생성합니다.
    - daily_messages: DB에서 가져온 전체 메시지 객체 리스트
                      [(channel_id, user_id, text, timestamp), ...]
    """
    if not client:
        return "OpenAI API 키가 설정되지 않았습니다."

    if not daily_messages:
        return "오늘 수집된 슬랙 메시지가 없어 요약할 내용이 없습니다."

    import datetime

    messages_str = ""
    for channel_id, user_id, text, timestamp in daily_messages:
        try:
            # Slack timestamp is a string representation of a float
            dt = datetime.datetime.fromtimestamp(float(timestamp))
            time_str = dt.strftime("%H:%M")
        except:
            time_str = timestamp
            
        messages_str += f"[Timestamp: {timestamp}] [KST: {time_str}] Channel: {channel_id} | User: {user_id} | Message: {text}\n"

    # 요약 프롬프트
    prompt = (
        "당신은 플러스위시드의 장 대표님을 보좌하는 든든하고 유쾌한 AI 비서실장 '위시드(WECYD)'입니다.\n"
        "다음은 오늘 전사 슬랙 채널 및 DM에서 수집된 업무 대화 로그입니다.\n"
        "이 로그를 바탕으로 요약 보고서를 작성해 주십시오.\n\n"
        "**[보고서 필수 출력 형식]**\n"
        "반드시 아래의 **JSON 형식**으로만 엄격하게 출력하세요. 절대 마크다운 코드 블록(```json 등)을 쓰지 마세요.\n"
        "{\n"
        '  "summary_list": [\n'
        '    {\n'
        '      "channel_name": "📌 [실제 채널명] 채널요약",\n'
        '      "overall_summary": "오늘 [채널명] 채널에서는 주로 [주제 A]에 대한 논의와 [주제 B] 관련 업무가 진행되었습니다. 특히...",\n'
        '      "messages": [\n'
        '        {\n'
        '          "time": "14:46",\n'
        '          "title": "사내 동호회 관련 공지사항",\n'
        '          "summary": "<@U1234567> 2026년 상반기 동호회 회원가입 및 신규 동호회 모집을 안내하고...",\n'
        '          "original_ts_list": ["1773294367.675659", "1773294380.123456"]\n'
        '        }\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        "}\n\n"
        "**[엄격한 주의사항 (필독)]**\n"
        "1. 제공된 대화 로그에 존재하는 모든 메시지를 누락 없이 최대한 상세하게 요약해야 합니다. 중요한 링크, 수치, 업무 지시 등은 절대 빼먹지 마세요.\n"
        "2. 비슷한 시간대의 같은 주제라면 하나로 묶어 작성하되, **세부적인 논의 사항이나 디테일한 발언 내용은 반드시 개조식으로 모두 포함**시키십시오.\n"
        "3. `overall_summary` 필드에는 해당 채널에서 오고 간 **전체적인 핵심 흐름과 주요 이슈를 종합적으로 요약**하십시오.\n"
        "4. `summary` 필드는 해당 대화(주제)의 세부 내용을 명확하고 상세한 개조식(bullet points)으로 요약하되, 요약 내용 앞에는 반드시 해당 발언을 한 슬랙 멘션 태그(예: <@U1234567>)를 포함하여 누가 무슨 말을 했는지 정확히 알 수 있게 하십시오.\n"
        "5. `original_ts_list`는 해당 주제/대화 묶음에 포함된 **모든 원문 메시지들의 Timestamp(ts) 값들을 배열(리스트) 형태**로 넣으십시오. (묶인 메시지가 여러 개라면 누락 없이 전부 배열에 넣어야 대화 원본 보기에서 모두 확인 가능합니다!)\n"
        "6. JSON 외에 어떠한 텍스트나 인사말도 덧붙이지 마십시오.\n"
        "7. `time`은 요약된 대화 묶음이 시작된 KST 시간입니다.\n\n"
        f"--- 오늘의 대화 로그 ---\n{messages_str}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=3000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f'{{"error": "AI 요약 생성 중 오류가 발생했습니다: {e}"}}'


def parse_calendar_query(question: str, now_kst: datetime) -> dict:
    """
    자연어 일정 질문을 파싱하여 start_datetime, end_datetime을 반환합니다.
    반환 형식: {"start": "YYYY-MM-DDTHH:MM:SS", "end": "YYYY-MM-DDTHH:MM:SS"}
    """
    if not client:
        return {}

    now_str = now_kst.strftime("%Y-%m-%d %H:%M (KST, %A)")
    prompt = (
        f"현재 시각: {now_str}\n\n"
        f"사용자 질문: \"{question}\"\n\n"
        "위 질문에서 조회하려는 일정의 시작 시각과 종료 시각을 파싱하세요.\n"
        "반드시 아래 JSON 형식으로만 답하세요:\n"
        "{\"start\": \"YYYY-MM-DDTHH:MM:SS\", \"end\": \"YYYY-MM-DDTHH:MM:SS\"}\n\n"
        "규칙:\n"
        "- '오늘 오전' → 오늘 00:00 ~ 12:00\n"
        "- '오늘 오후' → 오늘 12:00 ~ 23:59\n"
        "- '오늘' 또는 날짜 없으면 → 오늘 00:00 ~ 23:59\n"
        "- '이번주' → 오늘(현재 날짜)부터 이번 주 일요일 23:59까지\n"
        "- '다음주' → 다음 주 월요일 00:00부터 일요일 23:59까지\n"
        "- '이번달 12일' → 이번달 12일 00:00 ~ 23:59\n"
        "- JSON 외 다른 텍스트는 절대 출력하지 마세요."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        return {}


def parse_advanced_summary_query(question: str, now_kst: datetime) -> dict:
    """
    고급 요약 질문을 파싱하여 start, end, target_channel_name을 반환합니다.
    """
    if not client:
        return {}

    now_str = now_kst.strftime("%Y-%m-%d %H:%M:%S (KST, %A)")

    prompt = (
        f"현재 시각: {now_str}\n\n"
        f"사용자 질문: \"{question}\"\n\n"
        "위 질문에서 조회하려는 요약 대상의 시간 기간, 특정 대상 채널을 파싱하세요.\n\n"
        "반드시 아래 JSON 형식으로만 답하세요. 해당하는 값이 없으면 null로 설정하세요:\n"
        "{\"start\": \"YYYY-MM-DDTHH:MM:SS\", \"end\": \"YYYY-MM-DDTHH:MM:SS\", \"target_channel_name\": \"채널이름\"}\n\n"
        "시간 파싱 규칙:\n"
        "- 특정 일자/기간 언급이 없으면 기본값: 오늘 08:30:00 부터 현재 시각까지\n"
        "- '어제' → 어제 00:00:00 ~ 23:59:59\n"
        "- '16일' 등 특정 날짜 → 해당 날짜 00:00:00 ~ 23:59:59\n"
        "- '이번주' → 이번주 통째로\n\n"
        "채널 파싱 규칙:\n"
        "- 질문에서 특정 채널(예: 마케팅팀, 개발-기획, fos-업무소통 등)의 요약을 요구하면, 해당 채널 이름만 정확히 추출하여 target_channel_name에 넣으세요.\n"
        "- (주의) 슬랙 태그 <#C123|채널명> 형태로 들어오면, '채널명' 부분만 추출하세요.\n"
        "- (주의) 사용자가 '#채널명' 이라고 입력했으면 '#' 기호를 제외하고 이름만 추출하세요.\n"
        "- 매칭되는게 없거나 전체 요약을 요청하면 null로 설정하세요.\n"
        "- JSON 외 다른 텍스트는 절대 출력하지 마세요."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {}


def generate_meeting_comments(title: str, content: str) -> dict:
    """
    원고의 제목과 내용을 바탕으로 3명의 팀장(키워드, 에디터, 영상)의 코멘트를 생성합니다.
    - 위트 모드 적용: 각 캐릭터의 개성이 드러나고 재치 있는 말투 사용.
    """
    if not client:
        return {
            "keyword": "데이터 분석 중... (API 키 필요)",
            "editor": "원고 검토 중... (API 키 필요)",
            "video": "촬영 구상 중... (API 키 필요)"
        }

    prompt = (
        "당신은 '조간 에이전트 합동 회의'의 진행자이자 각 분야의 전문가 그룹입니다.\n"
        f"대상 원고: [{title}]\n"
        f"원고 내용 일부: {content[:1500]}\n\n"
        "다음 세 명의 팀장 페르소나에 맞춰 이 원고에 대한 짧고 재치 있는(위트 있는) 코멘트를 작성해 주세요.\n\n"
        "1. 📊 **키워드 팀장**: 시니어 타겟 트렌드 분석 및 SEO 전문가. 데이터와 숫자를 좋아하지만 말투는 능글맞고 유머러스함. 예상 CTR이나 검색량 추이를 언급.\n"
        "2. ✍️ **전문 에디터**: 5070 세대를 위한 신뢰감 있고 상샹한 건강 지식 에디터. 따뜻하지만 가끔 뼈 때리는 조언을 함. 맞춤법이나 가독성, 시니어 공감 요소를 언급.\n"
        "3. 🎬 **영상 팀장**: 유튜브 시청 이탈률 0%에 도전하는 디렉터. 트렌디하고 화이팅이 넘침. 쇼츠 연출 포인트나 썸네일 아이디어를 언급.\n\n"
        "**[출력 형식]**\n"
        "반드시 아래 JSON 형식으로만 응답하세요:\n"
        "{\n"
        '  "keyword": "코멘트 내용",\n'
        '  "editor": "코멘트 내용",\n'
        '  "video": "코멘트 내용"\n'
        "}\n"
        "각 코멘트는 1~2문장으로 아주 찰지고 재밌게 작성해 주세요."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"코멘트 생성 에러: {e}")
        return {
            "keyword": "아이고, 데이터 로딩 중에 커피를 쏟았네요!",
            "editor": "문장이 너무 좋아서 제가 잠시 넋을 잃었습니다.",
            "video": "카메라 렌즈 닦다가 타이밍을 놓쳤습니다!"
        }


def generate_image_prompts(title: str, content: str) -> list:
    """
    원고 내용을 분석하여 실사 스타일의 이미지 생성을 위한 고해상도 묘사 프롬프트 3개를 생성합니다.
    """
    if not client:
        return []

    prompt = (
        f"대상 원고: [{title}]\n"
        f"원고 내용 일부: {content[:1000]}\n\n"
        "위 원고에 삽입할 실사 사진(Real Photography) 스타일의 이미지 묘사 프롬프트 3개를 작성해 주세요.\n"
        "**[프롬프트 작성 규칙]**\n"
        "1. 스타일: AI 느낌이 나지 않는 아주 사실적이고 따뜻한 느낌의 한국인 시니어 대상 사진 스타일.\n"
        "2. 장면: 원고의 핵심 내용을 시각화할 것 (상황극, 장소, 사물 등).\n"
        "3. 언어: 영어로 출력하세요 (이미지 생성 도구용).\n"
        "4. 형식: 반드시 다른 설명 없이 각 프롬프트를 한 줄씩 리스트로만 출력하세요.\n"
        "예: 'A high-resolution photo of an elderly Korean woman smiling in a bright hospital room...'"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        # 줄 단위로 분리하여 리스트화
        lines = response.choices[0].message.content.strip().split('\n')
        return [l.strip('- ').strip('123. ') for l in lines if l.strip()]
    except Exception as e:
        print(f"이미지 프롬프트 생성 에러: {e}")
        return []


def generate_full_article_html(trend_keyword: str) -> str:
    """
    트렌드 키워드를 바탕으로 프리미엄 디자인이 적용된 전체 HTML 원고를 생성합니다.
    """
    if not client:
        return "OpenAI API 키가 설정되지 않았습니다."

    prompt = (
        f"당신은 5070 시니어를 위한 전문 에디터입니다. 주제: [{trend_keyword}]\n\n"
        "이 주제로 시니어들이 열광할 만한 프리미엄 블로그 포스팅을 HTML 형식으로 작성해 주세요.\n\n"
        "**[반드시 지켜야 할 가이드라인 - 분량 미달 시 재작성 필수]**\n"
        "1. 분량: **공백 포함 반드시 1,300자 ~ 1,500자 사이**로 작성하세요. (1,200자 이하는 실패임)\n"
        "   - 분량을 채우기 위한 필수 뼈대:\n"
        "     * [여는 글]: 주제와 관련된 시니어의 감동적인 사연 (350자 내외)\n"
        "     * [본문 1]: 제도의 상세 내용, 지원 금액, 신청 자격 (400자 내외)\n"
        "     * [본문 2]: 실제 신청 방법 5단계 및 주의사항 (300자 내외)\n"
        "     * [실제 사례]: 서로 다른 상황의 가상 사례 **3가지** (300자 내외)\n"
        "     * [자주 묻는 질문]: 핵심 질문 **6개**와 상세 답변 (350자 내외)\n"
        "2. 디자인: 기존 프리미엄 CSS 스타일을 유지하세요.\n"
        "3. 말투: 상냥하고 상세한 '건강 전문 에디터' 페르소나.\n"
        "4. 이미지: 원고 중간에 <img src='./images/placeholder.png' alt='...'> 위치를 **4군데** 비워두세요.\n\n"
        "**[CSS 스타일 코드 (파일에 포함시킬 것)]**\n"
        "<style>\n"
        "body { font-family: 'Pretendard', sans-serif; background-color: #f4f6f8; color: #1a1a1a; line-height: 1.8; }\n"
        ".kodari-article-box { max-width: 760px; margin: 0 auto; background-color: #ffffff; border-radius: 20px; padding: 40px; box-sizing: border-box; }\n"
        ".main-title { color: #d32f2f; font-size: 34px; font-weight: 900; text-align: center; border-bottom: 3px solid #ffebee; padding-bottom: 20px; }\n"
        ".highlight-box { background: linear-gradient(135deg, #fffde7, #fff59d); border-radius: 15px; padding: 30px; font-size: 26px; font-weight: 900; margin: 40px 0; }\n"
        ".body-text { font-size: 25px; margin-bottom: 35px; }\n"
        ".sub-title { color: #1976d2; font-size: 28px; font-weight: 800; margin: 45px 0 20px 0; display: flex; align-items: center; gap: 10px; }\n"
        ".emphasize { color: #c62828; font-weight: 900; background: linear-gradient(to top, #ffebee 40%, transparent 40%); }\n"
        ".quote-block { border-left: 6px solid #1565c0; background-color: #e3f2fd; padding: 25px 30px; margin: 35px 0; font-size: 24px; font-weight: bold; }\n"
        ".footer-call { background-color: #e8f5e9; border: 2px solid #a5d6a7; padding: 30px; text-align: center; border-radius: 15px; margin-top: 50px; }\n"
        ".bullet-list { list-style-type: none; padding-left: 0; }\n"
        ".bullet-list li { font-size: 25px; margin-bottom: 20px; padding-left: 35px; position: relative; }\n"
        ".bullet-list li::before { content: '✔️'; position: absolute; left: 0; top: 2px; }\n"
        "</style>"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"원고 생성 중 오류 발생: {e}"
