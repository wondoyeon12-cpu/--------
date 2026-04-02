import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_PATH = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH", "")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
KST = pytz.timezone("Asia/Seoul")


def _get_service():
    """구글 캘린더 API 서비스 클라이언트를 반환합니다."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=SCOPES
    )
    service = build("calendar", "v3", credentials=credentials)
    return service


def get_events(start_dt: datetime, end_dt: datetime) -> list:
    """
    지정된 시간 범위의 구글 캘린더 이벤트를 가져옵니다.
    - start_dt, end_dt: KST timezone aware datetime
    """
    if not CREDENTIALS_PATH or not os.path.exists(CREDENTIALS_PATH):
        print("[캘린더] 자격증명 파일이 없어 캘린더 조회를 건너뜁니다.")
        return []

    try:
        service = _get_service()
        time_min = start_dt.astimezone(pytz.utc).isoformat()
        time_max = end_dt.astimezone(pytz.utc).isoformat()

        result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=20
        ).execute()

        return result.get("items", [])
    except Exception as e:
        print(f"[캘린더] 이벤트 조회 실패: {e}")
        return []


def get_today_events() -> list:
    """오늘 하루 전체 이벤트를 가져옵니다."""
    now = datetime.now(KST)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    return get_events(start, end)


def get_events_by_date(year: int, month: int, day: int) -> list:
    """특정 날짜의 이벤트를 가져옵니다."""
    start = KST.localize(datetime(year, month, day, 0, 0, 0))
    end = KST.localize(datetime(year, month, day, 23, 59, 59))
    return get_events(start, end)


def get_events_in_range(start_dt: datetime, end_dt: datetime) -> list:
    """날짜 범위로 이벤트를 가져옵니다. (자연어 파싱 후 사용)"""
    return get_events(start_dt, end_dt)


def format_events_text(events: list, title: str = "*대표님! 오늘의 일정이 도착 했습니다! 📅 오늘 하루도 파이팅입니다!💪*") -> str:
    """
    이벤트 목록을 텍스트(슬랙/이메일 공통)로 포맷합니다.
    """
    if not events:
        return f"{title}\n등록된 일정이 없습니다."

    lines = [title]
    for event in events:
        summary = event.get("summary", "(제목 없음)")
        start = event.get("start", {})
        end = event.get("end", {})

        # 종일 일정 vs 시간 지정 일정
        if "dateTime" in start:
            start_dt = datetime.fromisoformat(start["dateTime"]).astimezone(KST)
            end_dt = datetime.fromisoformat(end["dateTime"]).astimezone(KST)
            time_str = f"{start_dt.strftime('%m/%d %H:%M')} ~ {end_dt.strftime('%H:%M')}"
        else:
            time_str = "종일"

        location = event.get("location", "")
        loc_str = f" | 📍 {location}" if location else ""
        lines.append(f"  • {time_str}  *{summary}*{loc_str}")

    return "\n".join(lines)


def format_events_html(events: list, title: str = "*대표님! 오늘의 일정이 도착 했습니다! 📅 오늘 하루도 파이팅입니다!💪*") -> str:
    """
    이벤트 목록을 이메일용 HTML로 포맷합니다.
    """
    if not events:
        return f"""
        <div style="background:#f0f4ff; border-left:4px solid #4A90E2; padding:12px 16px; border-radius:4px; margin-bottom:16px;">
          <strong style="color:#4A90E2;">{title}</strong><br>
          <span style="color:#888;">등록된 일정이 없습니다.</span>
        </div>"""

    rows = ""
    for event in events:
        summary = event.get("summary", "(제목 없음)")
        start = event.get("start", {})
        end = event.get("end", {})

        if "dateTime" in start:
            start_dt = datetime.fromisoformat(start["dateTime"]).astimezone(KST)
            end_dt = datetime.fromisoformat(end["dateTime"]).astimezone(KST)
            time_str = f"{start_dt.strftime('%m/%d %H:%M')} ~ {end_dt.strftime('%H:%M')}"
        else:
            time_str = "종일"

        location = event.get("location", "")
        loc_html = f" &nbsp;📍 {location}" if location else ""
        rows += f"""
        <tr>
          <td style="padding:6px 12px; color:#555; white-space:nowrap;">{time_str}</td>
          <td style="padding:6px 12px; font-weight:bold; color:#222;">{summary}{loc_html}</td>
        </tr>"""

    return f"""
    <div style="background:#f0f4ff; border-left:4px solid #4A90E2; padding:12px 16px; border-radius:4px; margin-bottom:16px;">
      <strong style="color:#4A90E2; font-size:15px;">{title}</strong>
      <table style="width:100%; border-collapse:collapse; margin-top:8px;">
        {rows}
      </table>
    </div>"""
