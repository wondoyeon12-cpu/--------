import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

USER_EMAIL = os.getenv("EMAIL_SENDER", "")
USER_PWD = os.getenv("EMAIL_PASSWORD", "")
TARGET_EMAIL = os.getenv("EMAIL_RECEIVER", "")

def send_daily_briefing(markdown_summary, calendar_html=None):
    """
    AI가 요약한 마크다운 + 구글 캘린더 일정을 HTML로 렌더링 후 SMTP로 발송합니다.
    """
    if not USER_EMAIL or not USER_PWD or not TARGET_EMAIL:
        print("이메일 설정(환경변수)이 누락되었습니다.")
        return False

    today_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"🔔 [위시드 비서실장] {today_str} 슬랙 일일 요약 브리핑"

    import re
    import html
    
    # 1. ACCORDION 마커 블록을 먼저 접이식 HTML로 치환 (이스케이프 전에 처리)
    def replace_accordion(match):
        raw_text = match.group(1).strip()
        escaped_raw = html.escape(raw_text)
        return (
            '<details style="margin: 6px 0 2px 0; border: 1px solid #dde3ee; border-radius: 6px; overflow: hidden;">'
            '<summary style="cursor: pointer; padding: 8px 12px; background: #f0f4ff; font-weight: bold; color: #4A90E2; list-style: none; user-select: none;">'
            '📄 대화 원문 보기 (클릭하여 펼치기)'
            '</summary>'
            '<pre style="margin: 0; padding: 12px 16px; background: #f9f9f9; white-space: pre-wrap; word-break: break-word; font-size: 13px; color: #333; font-family: \'Malgun Gothic\', Arial, sans-serif; line-height: 1.6;">'
            f'{escaped_raw}'
            '</pre>'
            '</details>'
        )

    def replace_comment_accordion(match):
        raw_text = match.group(1).strip()
        escaped_raw = html.escape(raw_text)
        return (
            '<details style="margin: 2px 0 10px 0; border: 1px solid #d4edcc; border-radius: 6px; overflow: hidden;">'
            '<summary style="cursor: pointer; padding: 8px 12px; background: #f0fff0; font-weight: bold; color: #3a8a3a; list-style: none; user-select: none;">'
            '💬 댓글 보기 (클릭하여 펼치기)'
            '</summary>'
            '<pre style="margin: 0; padding: 12px 16px; background: #f9fff9; white-space: pre-wrap; word-break: break-word; font-size: 13px; color: #333; font-family: \'Malgun Gothic\', Arial, sans-serif; line-height: 1.6;">'
            f'{escaped_raw}'
            '</pre>'
            '</details>'
        )

    # 마커 블록 치환 (이스케이프 전에 먼저 처리) - 원문 먼저, 댓글 다음
    processed_md = re.sub(
        r'%%ACCORDION_START%%\n(.*?)\n%%ACCORDION_END%%',
        replace_accordion,
        markdown_summary,
        flags=re.DOTALL
    )
    processed_md = re.sub(
        r'%%COMMENT_ACCORDION_START%%\n(.*?)\n%%COMMENT_ACCORDION_END%%',
        replace_comment_accordion,
        processed_md,
        flags=re.DOTALL
    )
    
    # 2. 나머지 텍스트에서 HTML 특수문자 이스케이프 처리
    #    (ACCORDION HTML 태그는 건드리지 않도록 플레이스홀더 방식 사용)
    PLACEHOLDER = "<<<ACCORDION_PLACEHOLDER_{idx}>>>"
    accordions = []
    
    def extract_accordion(m):
        accordions.append(m.group(0))
        return PLACEHOLDER.format(idx=len(accordions) - 1)
    
    # 접이식 HTML 블록을 임시 플레이스홀더로 보관
    text_only = re.sub(r'<details.*?</details>', extract_accordion, processed_md, flags=re.DOTALL)
    
    # 나머지 텍스트 이스케이프
    safe_md = html.escape(text_only)
    
    # 3. 볼드 처리 (*text* -> <strong>text</strong>)
    safe_md = re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', safe_md)
    
    # 4. 링크 처리 ([text](url) -> <a href="url">text</a>)
    safe_md = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" style="color: #4A90E2; text-decoration: none;">\1</a>', safe_md)
    
    # 5. 개행 처리 (\n -> <br>)
    safe_md = safe_md.replace('\n', '<br>')
    
    # 6. 플레이스홀더를 원래 접이식 HTML로 복원
    for idx, accordion_html in enumerate(accordions):
        safe_md = safe_md.replace(html.escape(PLACEHOLDER.format(idx=idx)), accordion_html)
    
    html_content = safe_md
    
    # 캘린더 섹션 (있으면 상단에 표시)
    calendar_section = calendar_html if calendar_html else ""

    html_template = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #4A90E2;">{today_str} 위시드 비서실장 아침 브리핑</h2>
        {calendar_section}
        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px;">
          {html_content}
        </div>
        <p style="margin-top: 20px; font-size: 0.9em; color: #777;">
          본 메일은 위시드 비서실장이 자동으로 요약하여 발송한 메일입니다.
        </p>
      </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['From'] = USER_EMAIL
    msg['To'] = TARGET_EMAIL
    msg['Subject'] = subject

    part = MIMEText(html_template, 'html')
    msg.attach(part)

    try:
        # Gmail SMTP 서버 (필요시 도메인 지원 SMTP로 변경)
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(USER_EMAIL, USER_PWD)
        server.sendmail(USER_EMAIL, TARGET_EMAIL, msg.as_string())
        server.quit()
        print("[이메일] 이메일 발송 완료!")
        return True
    except Exception as e:
        print(f"[이메일] 이메일 발송 실패: {e}")
        return False
