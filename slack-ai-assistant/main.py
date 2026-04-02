import os
import schedule
import time
import threading
from datetime import datetime
from dotenv import load_dotenv

import database
from ai_service import generate_daily_summary
from email_service import send_daily_briefing
from slack_bot import start_slack_bot
from calendar_service import get_today_events, format_events_text, format_events_html

load_dotenv()

def run_daily_routine():
    """
    1. 구글 캘린더에서 오늘 일정 조회
    2. 전날 슬랙 메시지 가져오기 및 AI 요약
    3. 슬랙 VIP 채널 + 이메일로 브리핑 발송
    4. DB 비우기
    """
    print(f"\n[{datetime.now()}] 데일리 루틴 시작 (08:30 자동 브리핑)")

    # 1. 오늘 캘린더 일정 조회
    print("[캘린더] 오늘 일정 조회 중...")
    today_events = get_today_events()
    calendar_slack_text = format_events_text(today_events, "*대표님! 오늘의 일정이 도착 했습니다! 📅 오늘 하루도 파이팅입니다!💪*")
    calendar_html = format_events_html(today_events, "*대표님! 오늘의 일정이 도착 했습니다! 📅 오늘 하루도 파이팅입니다!💪*")

    # 2. 전날 슬랙 메시지 가져오기
    messages = database.get_daily_messages()

    # 3. AI 요약 → 공통 빌더로 슬랙 블록 + 이메일 md_text 생성
    import json, re
    from slack_bot import build_briefing_blocks_and_text
    blocks = []
    md_text = ""
    data = {}
    if messages:
        print("AI가 슬랙 대화를 분석 중입니다...")
        summary_json = generate_daily_summary(messages)
        clean_json = summary_json.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r'^```[a-zA-Z]*\n?', '', clean_json)
        if clean_json.endswith("```"):
            clean_json = re.sub(r'\n?```$', '', clean_json)
        try:
            data = json.loads(clean_json)
        except Exception:
            data = {}
    # 4. 슬랙 VIP 채널에 캘린더 + 메시지 요약 발송
    VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID", "")
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    today_label = datetime.now().strftime("%Y.%m.%d")
    if VIP_CHANNEL_ID and SLACK_BOT_TOKEN:
        try:
            from slack_bolt import App
            slack_app = App(token=SLACK_BOT_TOKEN)

            # 이메일용/슬랙 멘션 치환을 위한 유저 목록 미리 가져오기
            user_map = {}
            try:
                users_res = slack_app.client.users_list()
                for u in users_res.get("members", []):
                    uid = u.get("id")
                    uname = u.get("real_name") or u.get("name")
                    if uid and uname:
                        user_map[f"<@{uid}>"] = f"@{uname}"
            except Exception:
                pass

            # 공통 빌더 호출 (수동 요청과 동일한 레이아웃)
            from slack_bot import build_briefing_blocks_and_text
            blocks, md_text = build_briefing_blocks_and_text(data, user_map)
            
            # 헤더 블록 (캘린더 포함) 추가
            header_text = f"*[위시드 비서실장] {today_label} 08:30 아침 브리핑 도착!*\n\n{calendar_slack_text}"
            header_block = {
                "type": "section",
                "text": {"type": "mrkdwn", "text": header_text}
            }
            blocks.insert(0, header_block)

            # 슬랙 메시지 요약 블록 (없을 경우 캘린더만 발송)
            chunk = []
            for b in blocks:
                chunk.append(b)
                if len(chunk) >= 45:
                    slack_app.client.chat_postMessage(
                        channel=VIP_CHANNEL_ID,
                        text="오늘의 요약 브리핑",
                        blocks=chunk
                    )
                    chunk = []
            if chunk:
                slack_app.client.chat_postMessage(
                    channel=VIP_CHANNEL_ID,
                    text="오늘의 요약 브리핑",
                    blocks=chunk
                )
        except Exception as e:
            print(f"[슬랙 브리핑 발송 실패] {e}")

    # 5. 이메일 발송 (캘린더 HTML + 슬랙 요약 함께)
    print("브리핑 이메일 전송 중...")
    send_daily_briefing(md_text, calendar_html=calendar_html)

    # 6. DB 비우기
    if messages:
        print("DB 정리 중...")
        database.clear_old_messages()

    print(f"[{datetime.now()}] 데일리 루틴 완료!")


def scheduler_thread():
    """백그라운드에서 스케줄러를 돌리는 스레드"""
    print("[scheduler] 스케줄러가 백그라운드에서 시작되었습니다. (매일 08:30 설정)")
    schedule.every().day.at("08:30").do(run_daily_routine)

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    # 1. DB 초기화 (테이블 생성 + 마이그레이션)
    database.init_db()

    # 2. 스케줄러 스레드 시작
    t = threading.Thread(target=scheduler_thread, daemon=True)
    t.start()

    # 3. 메인 스레드에서 Slack Bolt 앱 실행
    start_slack_bot()


if __name__ == "__main__":
    main()
