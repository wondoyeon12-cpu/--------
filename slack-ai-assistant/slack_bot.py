import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

from database import save_message, get_recent_messages
from ai_service import get_ai_answer

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

app = App(token=SLACK_BOT_TOKEN)

# 모든 채널, 그룹방, 개인DM 메시지 수신 이벤트 
@app.event("message")
def handle_message_events(body, logger):
    event = body.get("event", {})
    # channel_id는 공개/비공개/DM 모두 'channel' 키에 들어옵니다
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    ts = event.get("ts")

    print(f"[디버그] 일반 메시지 감지됨! (유저: {user_id}, 텍스트 길이: {len(text) if text else 0})")

    # 봇 자신의 메시지이거나, 내용이 없으면 패스
    if event.get("bot_id") is not None or not text:
        print("[디버그] 봇 자신의 메시지이거나 빈 텍스트라 무시합니다.")
        return

    # 사용자 ID를 이름으로 보낼 경우 태그 멘션이 되도록 <@user_id> 로 저장합니다
    user_name = f"<@{user_id}>"

    # 쓰레드 답글 여부 판단 (thread_ts가 있고 ts와 다르면 답글)
    thread_ts = event.get("thread_ts")

    # 채널 ID를 실제 이름으로 변환 (AI가 'C09D1E6EU5A' 등이 아닌 실제 방 이름을 알 수 있게)
    channel_name = channel_id
    try:
        channel_info = app.client.conversations_info(channel=channel_id)
        if channel_info.get("ok"):
            channel = channel_info.get("channel", {})
            channel_name = channel.get("name") or "개인 DM"
    except Exception as e:
        logger.error(f"채널 정보 가져오기 실패: {e}")

    # 메시지 DB 저장 (ID 대신 직접 이름 저장, thread_ts 함께 저장)
    save_message(channel_name, user_name, text, ts, thread_ts=thread_ts)
    print(f"[debug] DB 저장 완료: [채널: {channel_name}] 유저 {user_name} (답글여부: {thread_ts and thread_ts != ts})")

def build_briefing_blocks_and_text(data: dict, user_map: dict, logger=None) -> tuple:
    """
    AI 요약 JSON 데이터로 슬랙 블록 + 이메일 md_text를 빌드합니다.
    Returns: (blocks, md_text)
    """
    import datetime
    from database import get_message_by_ts, get_replies_by_thread_ts

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*충성! 위시드 비서 실장입니다! :saluting_face: 대표님! 슬랙 업무 채팅 내용 요약 보고 드립니다!*"
            }
        }
    ]
    md_text = "*충성! 위시드 비서 실장입니다! 🫡 대표님! 슬랙 업무 채팅 내용 요약 보고 드립니다!*\n\n"

    for ch in data.get("summary_list", []):
        channel_name = ch.get("channel_name", "채널")
        overall_summary = ch.get("overall_summary", "")

        text_content = f"*{channel_name}*\n"
        md_content = f"*{channel_name}*\n\n"
        
        if overall_summary:
            text_content += f"> *전체 대화 요약*\n> {overall_summary}\n\n"
            md_content += f"**전체 대화 요약**\n{overall_summary}\n\n"
            
        text_content += "- :clock3: 대화 타임라인:\n"
        md_content += "- 대화 타임라인:\n\n"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text_content
            }
        })
        md_text += md_content

        for msg in ch.get("messages", []):
            m_time = msg.get("time", "")
            m_title = msg.get("title", "")
            m_summary = msg.get("summary", "")
            
            # 배열(list) 혹은 단일 문자열 호환
            m_ts_val = msg.get("original_ts_list") or msg.get("original_ts", "")
            if isinstance(m_ts_val, list):
                m_ts_list = [str(t).strip() for t in m_ts_val if t]
            else:
                m_ts_list = [str(m_ts_val).strip()] if m_ts_val else []
            
            m_ts = ",".join(m_ts_list)  # Join to a single string for button value

            text_block = f"*[ {m_time} ] {m_title}*\n{m_summary}"
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": text_block}
            })

            if m_ts_list:
                raw_lines = []
                replies = []
                for current_ts in m_ts_list:
                    # 원문 가져오기
                    try:
                        raw_row = get_message_by_ts(current_ts)
                        if raw_row:
                            r_channel, r_user, r_text, r_ts = raw_row
                            try:
                                r_dt = datetime.datetime.fromtimestamp(float(r_ts))
                                r_time = r_dt.strftime("%H:%M")
                            except Exception:
                                r_time = str(r_ts)
                            r_text_display = r_text
                            for mention, name in user_map.items():
                                r_text_display = r_text_display.replace(mention, name)
                            raw_lines.append(f"[{r_time}] {r_user}\n{r_text_display}")
                    except Exception as e:
                        if logger:
                            logger.error(f"원문 조회 실패 (ts={current_ts}): {e}")

                    # 쓰레드 답글 가져오기
                    try:
                        reply_rows = get_replies_by_thread_ts(current_ts)
                        for r_user, r_text, r_ts in reply_rows:
                            try:
                                r_dt = datetime.datetime.fromtimestamp(float(r_ts))
                                r_time = r_dt.strftime("%H:%M")
                            except Exception:
                                r_time = str(r_ts)
                            r_text_display = r_text
                            for mention, name in user_map.items():
                                r_text_display = r_text_display.replace(mention, name)
                            replies.append(f"[{r_time}] {r_user}\n{r_text_display}")
                    except Exception as e:
                        if logger:
                            logger.error(f"댓글 조회 실패 (ts={current_ts}): {e}")

                action_elements = [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "emoji": True, "text": "📄 대화 원문 보기"},
                        "value": str(m_ts),
                        "action_id": "open_single_raw_log_modal"
                    }
                ]
                if replies:
                    modal_value = "\n\n".join(replies)[:1900]
                    action_elements.append({
                        "type": "button",
                        "text": {"type": "plain_text", "emoji": True, "text": f"💬 댓글 보기 ({len(replies)}개)"},
                        "value": modal_value,
                        "action_id": "open_reply_modal"
                    })
                blocks.append({"type": "actions", "elements": action_elements})

                if raw_lines:
                    raw_content = "\n".join(raw_lines)
                    md_text += f"{text_block}\n%%ACCORDION_START%%\n{raw_content}\n%%ACCORDION_END%%\n"
                else:
                    md_text += f"{text_block}\n"

                if replies:
                    reply_content = "\n\n".join(replies)
                    md_text += f"%%COMMENT_ACCORDION_START%%\n{reply_content}\n%%COMMENT_ACCORDION_END%%\n\n"
                else:
                    md_text += "\n"
            else:
                md_text += f"{text_block}\n\n"

    footer_text = "저 위시드는 언제든 대표님의 얘기에 귀기울일 준비가 되어 있습니다! 언제든 불러주십쇼 😎"
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": footer_text}
    })
    md_text += footer_text

    import re
    for mention, name in user_map.items():
        if mention in md_text:
            md_text = md_text.replace(mention, name)
    md_text = re.sub(r'<@U[A-Z0-9]+>', lambda m: m.group(0).replace('<', '').replace('>', ''), md_text)

    return blocks, md_text


# 봇을 @태그 (app_mention) 했을 때 질의응답 처리
@app.event("app_mention")
def handle_app_mention_events(body, say, logger):
    event = body.get("event", {})
    channel_id = event.get("channel")
    text = event.get("text", "")
    
    print(f"[디버그] 봇이 멘션되었습니다! (내용 길이: {len(text) if text else 0})")
    
    # 채널 입장 시 자동 멘션 등 텍스트 없는 경우 무시
    if not text or text.strip() == "":
        return
    
    VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID", "")

    # 캘린더 일정 조회 요청 여부
    CALENDAR_KEYWORDS = ["일정", "캘린더", "스케줄", "스케쥴", "미팅", "회의", "약속", "오늘 뭐해", "일과", "일정표", "오늘 할일", "오늘 뭐", "오늘 스케줄"]
    wants_calendar = any(kw in text for kw in CALENDAR_KEYWORDS)
    
    # 요약/브리핑 요청 여부
    SUMMARY_KEYWORDS = ["요약", "보고", "브리핑", "레포트", "정리해줘", "알려줘", "대화내용", "채팅", "무슨 일", "무슨일", "정리"]
    wants_summary = any(kw in text for kw in SUMMARY_KEYWORDS)
    
    # 캘린더 요청("일정 알려줘", "일정 보고해줘" 등)과 요약 키워드가 충돌할 때 예외 처리
    if wants_calendar:
        # 강력한 요약 키워드(대화, 채팅, 요약, 브리핑 등)가 없으면 요약하지 않고 일정만 조회
        strong_summary_kws = ["대화", "채팅", "요약", "브리핑", "레포트", "무슨일"]
        if not any(kw in text.replace(" ", "") for kw in strong_summary_kws):
            wants_summary = False

    if wants_calendar:
        say(":calendar: [위시드 비서실장] 일정 조회 중입니다! 잠시만요 🔍")
        try:
            from datetime import datetime
            import pytz
            from calendar_service import get_events_in_range, format_events_text
            from ai_service import parse_calendar_query

            KST = pytz.timezone("Asia/Seoul")
            now_kst = datetime.now(KST)

            # AI로 날짜 파싱
            parsed = parse_calendar_query(text, now_kst)
            if parsed.get("start") and parsed.get("end"):
                start_dt = KST.localize(datetime.fromisoformat(parsed["start"]))
                end_dt = KST.localize(datetime.fromisoformat(parsed["end"]))
                events = get_events_in_range(start_dt, end_dt)
                
                if start_dt.date() == end_dt.date():
                    date_label = f"{start_dt.strftime('%m/%d')} 일정"
                else:
                    date_label = f"{start_dt.strftime('%m/%d')} ~ {end_dt.strftime('%m/%d')} 일정"
                    
                result_text = format_events_text(events, f"📅 {date_label}")
            else:
                from calendar_service import get_today_events
                events = get_today_events()
                result_text = format_events_text(events, "*대표님! 오늘의 일정이 도착 했습니다! 📅 오늘 하루도 파이팅입니다!💪*")

            say(f":saluting_face: [위시드 비서실장] 일정 조회 완료!\n\n{result_text}")
        except Exception as e:
            logger.error(f"캘린더 조회 실패: {e}")
            say(f"죄송합니다, 일정 조회 중 오류가 발생했습니다. 구글 캘린더 연동 설정을 확인해주세요.")
        
        # 만약 요약 요청이 없다면 여기서 끝내도 됨
        if not wants_summary:
            say("저 위시드는 언제든 대표님의 얘기에 귀기울일 준비가 되어 있습니다! 😎")
            return

    # 요약/브리핑 요청인 경우 → VIP 채널에서만 허용
    if wants_summary:
        if channel_id != VIP_CHANNEL_ID:
            say("💬 [위시드 비서실장] 요약 브리핑은 지정된 VIP 보고 채널에서만 요청하실 수 있습니다. 이 채널의 대화는 정상적으로 수집 중이니 안심하십시오! 😊")
            return
        
        say(":saluting_face: [위시드 비서실장] 대표님! 전사 채널 대화를 쫙 수집해서 요약 브리핑을 준비 중입니다. 잠시만 기다려주십시오! :rocket:")

        from datetime import datetime
        import pytz
        KST = pytz.timezone("Asia/Seoul")
        now_kst = datetime.now(KST)

        # 1. AI 질의 파싱
        from ai_service import parse_advanced_summary_query, generate_daily_summary
        parsed_summary = parse_advanced_summary_query(text, now_kst)
        
        start_ts_str = parsed_summary.get("start")
        end_ts_str = parsed_summary.get("end")
        target_channel = parsed_summary.get("target_channel_name")

        if not start_ts_str or not end_ts_str:
            # 기본값 오늘 08:30 ~ 현재
            start_dt = now_kst.replace(hour=8, minute=30, second=0, microsecond=0)
            end_dt = now_kst
        else:
            start_dt = KST.localize(datetime.fromisoformat(start_ts_str))
            end_dt = KST.localize(datetime.fromisoformat(end_ts_str))

        start_unix = str(start_dt.timestamp())
        end_unix = str(end_dt.timestamp())

        # 2. 메시지 가져오기
        from database import get_filtered_messages
        daily_messages = get_filtered_messages(start_unix, end_unix, target_channel)
        
        if not daily_messages:
            say("해당 조건에 맞는 대화 내용이 없습니다.")
            return
            
        # 3. 필터 정보 알림
        filter_lines = [f"📅 요약 범위: {start_dt.strftime('%m/%d %H:%M')} ~ {end_dt.strftime('%m/%d %H:%M')}"]
        if target_channel:
            filter_lines.append(f"📍 대상 채널: {target_channel}")
            
        filter_text = " | ".join(filter_lines)
        say(f"선택하신 조건으로 요약합니다!\n> {filter_text}")

        # 4. 요약 생성
        summary_json = generate_daily_summary(daily_messages)

        import json
        import re
        
        # AI가 ```json 과 같은 마크다운 블록을 보낼 경우를 대비해 텍스트 정제
        clean_json = summary_json.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r'^```[a-zA-Z]*\n?', '', clean_json)
        if clean_json.endswith("```"):
            clean_json = re.sub(r'\n?```$', '', clean_json)
        clean_json = clean_json.strip()

        try:
            data = json.loads(clean_json)
        except Exception as e:
            logger.error(f"JSON 파싱 에러: {e}\n원본데이터: {summary_json}")
            say("요약 생성에 실패했습니다. (JSON 데이터 파싱 오류 - 응답이 너무 길어 끊겼을 수 있습니다.)")
            return
            
        # 워크스페이스 도메인 가져오기 (이메일 링크용)
        try:
            team_info = app.client.team_info()
            team_domain = team_info["team"]["domain"]
        except Exception as e:
            logger.error(f"팀 정보 가져오기 실패: {e}")
            team_domain = "app"
            
        # 이메일용 멘션 치환을 위한 유저 목록 미리 가져오기
        user_map = {}
        try:
            users_res = app.client.users_list()
            for u in users_res.get("members", []):
                uid = u.get("id")
                uname = u.get("real_name") or u.get("name")
                if uid and uname:
                    user_map[f"<@{uid}>"] = f"@{uname}"
        except Exception as e:
            logger.error(f"유저 목록 가져오기 실패: {e}")

        # 공통 빌더로 블록 + md_text 생성
        blocks, md_text = build_briefing_blocks_and_text(data, user_map, logger)

        # 블록 전송 (최대 50개 제한 쪼개기)
        chunk = []
        for b in blocks:
            chunk.append(b)
            if len(chunk) >= 45:
                say(text="오늘의 요약 브리핑 도착", blocks=chunk)
                chunk = []
        if chunk:
            say(text="오늘의 요약 브리핑 도착", blocks=chunk)

        from email_service import send_daily_briefing
        email_success = send_daily_briefing(md_text)
        if email_success:
            say("📧 [위시드 비서실장] 요약 브리핑을 대표님의 이메일로도 무사히 발송 완료했습니다!")
    else:
        # 일반 질문인 경우 최근 대화 맥락과 함께 AI 답변 생성
        from database import get_recent_messages
        from ai_service import get_ai_answer
        
        recent_history = get_recent_messages(channel_id, limit=30)
        answer = get_ai_answer(text, recent_history)
        say(answer)


# 개별 대화 원문 보기 버튼 클릭 시 띄울 모달창
@app.action("open_single_raw_log_modal")
def handle_open_single_raw_log_modal(ack, body, client, logger):
    ack()
    
    try:
        ts_val = body["actions"][0].get("value")
        if not ts_val:
            return
            
        from database import get_message_by_ts
        import datetime
        
        ts_list = [t.strip() for t in ts_val.split(",") if t.strip()]
        raw_texts = []
        
        for ts in ts_list:
            row = get_message_by_ts(ts)
            if row:
                channel, user, text, db_ts = row
                try:
                    dt = datetime.datetime.fromtimestamp(float(db_ts))
                    t = dt.strftime("%H:%M")
                except:
                    t = db_ts
                raw_texts.append(f"[{t}] {user}\n{text}")
                
        if not raw_texts:
            raw_text = "메시지 원본을 데이터베이스에서 찾을 수 없습니다."
        else:
            raw_text = "\n\n---\n\n".join(raw_texts)
            
        safe_raw_text = raw_text[:2900] + ("\n...(생략됨)" if len(raw_text) > 2900 else "")

        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "대화 원문 보기"},
                "close": {"type": "plain_text", "text": "닫기"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{safe_raw_text}```"
                        }
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"단일 모달 열기 에러: {e}")


# 댓글 보기 버튼 클릭 시 모달창 (value에 저장된 댓글 텍스트를 그대로 표시)
@app.action("open_reply_modal")
def handle_open_reply_modal(ack, body, client, logger):
    ack()

    try:
        reply_text = body["actions"][0].get("value", "댓글을 찾을 수 없습니다.")
        safe_reply_text = reply_text[:2900] + ("\n...(생략됨)" if len(reply_text) > 2900 else "")

        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "title": {"type": "plain_text", "text": "💬 댓글 보기"},
                "close": {"type": "plain_text", "text": "닫기"},
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{safe_reply_text}```"
                        }
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"댓글 모달 열기 에러: {e}")

def start_slack_bot():
    """소켓 모드 핸들러로 슬랙 봇을 실행합니다."""
    print("Slack Bolt 앱 실행 중...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

# 테스트용 로컬 직접 실행
if __name__ == "__main__":
    start_slack_bot()
