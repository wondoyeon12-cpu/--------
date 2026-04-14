import os
import schedule
import time
import threading
from datetime import datetime
from dotenv import load_dotenv

import database
from ai_service import generate_daily_summary
from email_service import send_daily_briefing
from slack_bot import start_slack_bot, backfill_missed_messages, app
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

    # 2. 전날 슬랙 메시지 가져오기 (마지막 성공 시점 이후부터)
    last_ts = database.get_last_briefing_time("morning")
    messages = database.get_daily_messages(start_ts=last_ts)

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

    # 5. DB 비우기
    if messages:
        print("DB 정리 중...")
        database.clear_old_messages()

    # 6. 실행 완료 로그 기록
    database.log_briefing_sent("morning")

    print(f"[{datetime.now()}] 데일리 루틴 완료!")


def run_afternoon_email_routine():
    """
    매일 17:25 에 실행되어 마지막 성공 시점부터 현재까지 발생한 대화를 모아 AI 요약 후 '이메일'로만 전송합니다.
    """
    print(f"\n[{datetime.now()}] 오후 루틴 시작 (17:25 이메일 브리핑)")
    
    # 마지막 성공 시점 이후부터 현재까지 수동 수집
    last_ts = database.get_last_briefing_time("afternoon")
    end_unix = str(datetime.now().timestamp())
    
    # 메시지 가져오기
    from database import get_filtered_messages
    messages = get_filtered_messages(start_ts=last_ts, end_ts=end_unix)

    if not messages:
        print("금일 수집된 메시지가 없어 이메일 발송을 생략합니다.")
        return

    print("AI가 오늘 업무시간 슬랙 대화를 분석 중입니다...")
    summary_json = generate_daily_summary(messages)
    
    import json, re
    clean_json = summary_json.strip()
    if clean_json.startswith("```"):
        clean_json = re.sub(r'^```[a-zA-Z]*\n?', '', clean_json)
    if clean_json.endswith("```"):
        clean_json = re.sub(r'\n?```$', '', clean_json)
    try:
        data = json.loads(clean_json)
    except Exception as e:
        print(f"JSON 파싱 에러: {e}")
        return

    # 유저 맵
    user_map = {}
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    if SLACK_BOT_TOKEN:
        try:
            from slack_bolt import App
            slack_app = App(token=SLACK_BOT_TOKEN)
            users_res = slack_app.client.users_list()
            for u in users_res.get("members", []):
                uid = u.get("id")
                uname = u.get("real_name") or u.get("name")
                if uid and uname:
                    user_map[f"<@{uid}>"] = f"@{uname}"
        except Exception:
            pass

    from slack_bot import build_briefing_blocks_and_text
    _, md_text = build_briefing_blocks_and_text(data, user_map)

    print("오후 브리핑 이메일 전송 중...")
    send_daily_briefing(md_text, calendar_html=None)
    
    # 실행 완료 로그 기록
    database.log_briefing_sent("afternoon")
    
    print(f"[{datetime.now()}] 오후 루틴 완료!")


def scheduler_thread():
    """백그라운드에서 스케줄러를 돌리는 스레드"""
    print("[scheduler] 스케줄러가 백그라운드에서 시작되었습니다. (매일 08:30 슬랙, 17:25 이메일 설정)")
    schedule.every().day.at("08:30").do(run_daily_routine)
    schedule.every().day.at("17:25").do(run_afternoon_email_routine)

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    # 1. DB 초기화 (테이블 생성 + 마이그레이션)
    database.init_db()

    # 2. 부재중 메시지 백필 수행 (브리핑 전 최신화)
    print(f"[{datetime.now()}] 부재중 메시지 수집 시작...")
    try:
        backfill_missed_messages(app)
    except Exception as e:
        print(f"[메인 백필 에러] {e}")

    # 3. 누적형(Cumulative) 브리핑 체크 (컴퓨터를 늦게 켰거나 누락된 경우)
    # 주말 제외 (0=월, 4=금, 5=토, 6=일)
    if datetime.now().weekday() < 5:
        now = datetime.now()
        
        # A. 아침 브리핑 체크 (08:30 이후)
        if not database.is_briefing_sent_today("morning"):
            if (now.hour > 8) or (now.hour == 8 and now.minute >= 30):
                print(f"[{now}] 08:30 아침 브리핑 누락 감지 -> 즉시 발송 루틴 시작")
                threading.Thread(target=run_daily_routine, daemon=True).start()
        
        # B. 오후 브리핑 체크 (17:25 이후)
        if not database.is_briefing_sent_today("afternoon"):
            if (now.hour > 17) or (now.hour == 17 and now.minute >= 25):
                print(f"[{now}] 17:25 오후 이메일 브리핑 누락 감지 -> 즉시 발송 루틴 시작")
                threading.Thread(target=run_afternoon_email_routine, daemon=True).start()

    # 4. 스케줄러 스레드 시작
    t = threading.Thread(target=scheduler_thread, daemon=True)
    t.start()

    # 5. 메인 스레드에서 Slack Bolt 앱 실행
    start_slack_bot()


if __name__ == "__main__":
    main()
