import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def create_email_html(articles):
    """Jinja2를 사용하여 기사 데이터를 HTML 템플릿에 렌더링"""
    # 템플릿 폴더가 없으면 현재 디렉토리에서 찾음
    env = Environment(loader=FileSystemLoader('.'))
    
    # 템플릿 파일이 없는 경우를 위한 기본 HTML 스트링 템플릿
    template_str = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <style>
            /* Google Fonts for Typography matching */
            @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,700;0,900;1,300&display=swap');
            
            body { font-family: 'Inter', 'Apple SD Gothic Neo', sans-serif; background-color: #eef1f5; padding: 30px; color: #333333; margin: 0; }
            .container { max-width: 850px; margin: 0 auto; background: #ffffff; padding: 0; border-radius: 6px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
            
            /* Enhanced Corporate Header with gentle background box */
            .header { padding: 45px 50px 35px 50px; background-color: #f4f6fa; border-bottom: 1px solid #e1e7f0; }
            .header-top { text-align: left; }
            .fos-logo { font-size: 58px; font-weight: 900; color: #0b1e40; letter-spacing: -2px; margin-right: 15px; }
            .insights-logo { font-size: 58px; font-weight: 300; font-style: italic; color: #0b1e40; }
            .header-subtitle { font-size: 15px; font-weight: 400; color: #475569; margin-top: 12px; line-height: 1.5; letter-spacing: -0.5px; }
            .header-meta { font-size: 13px; color: #64748b; text-transform: uppercase; letter-spacing: 2px; margin-top: 20px; font-weight: bold; }

            /* Premium Section Badge/Title */
            .section-title { font-size: 14px; font-weight: 800; color: #0078d4; margin-bottom: 25px; padding: 4px 12px; border-radius: 4px; background: rgba(0, 120, 212, 0.1); display: inline-block; text-transform: uppercase; letter-spacing: 1px; }
            .section-title-dark { font-size: 14px; font-weight: 800; color: #0b1e40; margin-bottom: 25px; padding: 4px 12px; border-radius: 4px; background: rgba(11, 30, 64, 0.08); display: inline-block; text-transform: uppercase; letter-spacing: 1px; }

            /* Grid Layout */
            .content-wrapper { display: table; width: 100%; box-sizing: border-box; padding: 25px 30px; background-color: #ffffff; }
            .left-column { display: table-cell; width: 65%; vertical-align: top; padding-right: 15px; box-sizing: border-box; }
            .right-column { display: table-cell; width: 35%; vertical-align: top; padding-left: 15px; box-sizing: border-box; }
            
            /* Section 1: Cover Story (Left Col) */
            .cover-section { padding: 35px; background-color: #f4f6fa; border-radius: 12px; margin-bottom: 25px; border: 1px solid #eef1f6; }
            .cover-card { background: #ffffff; border: 1px solid #e1e7f0; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.04); overflow: hidden; }
            .cover-img { width: 100%; height: auto; max-height: 400px; object-fit: cover; border-bottom: 1px solid #e2e8f0; display: block; }
            .cover-title { font-size: 32px; font-weight: 900; color: #0b1e40; line-height: 1.35; text-decoration: none; display: block; letter-spacing: -0.5px;}
            .cover-body { padding: 30px; }
            .cover-title:hover { color: #0078d4; }
            .cover-snippet { font-size: 16px; color: #475569; line-height: 1.6; }

            /* Section 2: Deep Insights (Left Col Cards) Alignment Fix */
            .insights-section { height: 439.75px; max-height: 439.75px; display: block; padding: 35px; background-color: #f4f6fa; border-radius: 12px; border: 1px solid #eef1f6; box-sizing: border-box; overflow: hidden; }
            /* border-spacing 제거하고 일반 div 래퍼로 교체하여 padding으로 간격 조정 (좌측 외곽선 오차 1px 해결) */
            .two-col-container { display: table; width: 100%; border-collapse: collapse; }
            .insight-card-wrapper-left { display: table-cell; width: 50%; vertical-align: top; padding-right: 10px; box-sizing: border-box; }
            .insight-card-wrapper-right { display: table-cell; width: 50%; vertical-align: top; padding-left: 10px; box-sizing: border-box; }
            
            .insight-card { display: block; background: #ffffff; border: 1px solid #e1e7f0; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.04); overflow: hidden; height: 313.75px; max-height: 313.75px; box-sizing: border-box; }
            .insight-img { width: 100%; height: 160px; object-fit: cover; background: #f8fafc; border-bottom: 1px solid #e1e7f0; display: block; }
            .insight-body { padding: 25px; box-sizing: border-box; }
            .insight-title { font-size: 18px; font-weight: 800; color: #111111 !important; line-height: 1.4; text-decoration: none; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; max-height: 100px; letter-spacing: -0.5px; transition: color 0.25s ease; }
            .insight-title:hover { color: #0078d4 !important; }

            /* Section 3: Industry Pulse (Right Col Sidebar Text-Only) */
            .briefs-section { flex-grow: 1; padding: 40px 30px; box-sizing: border-box; background-color: #eff3f7; border-radius: 12px; border: 1px solid #e9edf3; }
            .brief-item { padding-bottom: 25px; margin-bottom: 25px; border-bottom: 1px solid #e2e8f0; }
            .brief-item:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: none; }
            /* Title is BOLD, Snippet is normal weight. Add smooth color transition */
            .brief-title { font-size: 18px; font-weight: 800; color: #111111 !important; line-height: 1.4; text-decoration: none; display: block; margin-bottom: 12px; transition: color 0.25s ease;}
            .brief-title:hover { color: #0078d4 !important; }
            .brief-snippet { font-size: 14px; font-weight: 400; color: #111111 !important; line-height: 1.6; transition: color 0.25s ease; }
            .brief-snippet:hover { color: #0078d4 !important; }

            /* Bottom CTA */
            .cta-section { background-color: #0b1e40; padding: 60px 40px; text-align: center; border-bottom: 8px solid #0078d4; }
            .cta-button { display: inline-block; background-color: #0078d4; color: #ffffff; text-decoration: none; padding: 18px 45px; font-weight: 700; font-size: 16px; border-radius: 4px; margin: 10px; text-transform: uppercase; letter-spacing: 1px; transition: background 0.3s; }
            .cta-button:hover { background-color: #005a9e; }
            .cta-subtext { color: #8ba0b5; font-size: 12px; margin-top: 30px; line-height: 1.6; text-transform: uppercase; letter-spacing: 0.5px;}

            @media screen and (max-width: 650px) {
                body { padding: 10px; }
                .header, .cover-section, .insights-section, .briefs-section, .cta-section { padding: 25px; }
                .fos-logo, .insights-logo { font-size: 42px; }
                
                /* Override table display for mobile stacking */
                .content-wrapper { display: block; padding: 0; }
                .left-column, .right-column { display: block; width: 100%; padding: 0 !important; }
                
                /* Left column elements first (Main Report, Deep Insights) */
                .cover-section, .insights-section { margin-bottom: 25px; }
                .insights-section { height: auto !important; max-height: none !important; }
                
                /* Inside Deep Insights, stack the two cards */
                .two-col-container { display: block; width: 100%; }
                .insight-card-wrapper-left, .insight-card-wrapper-right { display: block; width: 100%; padding: 0 !important; margin-bottom: 25px; }
                .insight-card-wrapper-right { margin-bottom: 0; }
                
                /* Reset card heights on mobile to fit content naturally */
                .insight-card { display: block; width: 100%; height: auto !important; max-height: none !important; box-sizing: border-box; margin-bottom: 0; }
                .insight-title { max-height: none; -webkit-line-clamp: unset; }
                
                .cta-button { display: block; margin: 10px 0; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            
            <!-- Corporate Header with Background Box -->
            <div class="header">
                <div class="header-top">
                    <span class="fos-logo">FOS</span><span class="insights-logo">Insights</span>
                    <div class="header-subtitle">FOS에서 분석한 프랜차이즈 운영의 변곡점, FOS Insights에서 전해드립니다.</div>
                    <div class="header-meta">NEWSLETTER | {{ today_date }} | VOL. 12</div>
                </div>
            </div>

            <!-- Content Grid Wrapper -->
            <div class="content-wrapper">
                
                <!-- LEFT COLUMN -->
                <div class="left-column">
                    {% if articles and articles|length >= 1 %}
                    <!-- Section 1: Cover Story (1 Col) -->
                    <div class="cover-section">
                        <div class="section-title">Main Report</div>
                        {% set cover = articles[0] %}
                        <div class="cover-card">
                            {% if cover.thumbnail %}
                            <img src="{{ cover.thumbnail }}" alt="메인 기사 이미지" class="cover-img">
                            {% endif %}
                            <div class="cover-body">
                                <a href="{{ cover.link }}" class="cover-title" target="_blank" style="text-decoration:none; transition: color 0.25s ease;">{{ cover.title }}</a>
                            </div>
                        </div>
                    </div>
                    {% endif %}

                    <!-- Section 2: Deep Insights (2 Col Cards) -->
                    {% if articles|length >= 3 %}
                    <div class="insights-section">
                        <div class="section-title">Deep Insights</div>
                        <div class="two-col-container">
                            {% for insight in articles[1:3] %}
                            <div class="{{ 'insight-card-wrapper-left' if loop.index0 == 0 else 'insight-card-wrapper-right' }}">
                                <div class="insight-card">
                                    {% if insight.thumbnail %}
                                    <img src="{{ insight.thumbnail }}" alt="인사이트 썸네일" class="insight-img">
                                    {% else %}
                                    <div class="insight-img" style="line-height:160px; text-align:center; color:#94a3b8; font-size:14px; background:#f1f5f9;">NO IMAGE</div>
                                    {% endif %}
                                    <div class="insight-body">
                                        <a href="{{ insight.link }}" class="insight-title" target="_blank">{{ insight.title }}</a>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>

                <!-- RIGHT COLUMN -->
                <div class="right-column">
                    <!-- Section 3: Industry Pulse (Right Text-Only Sidebar) -->
                    {% if articles|length >= 4 %}
                    <div class="briefs-section">
                        <div class="section-title-dark">Industry Pulse</div>
                        {% for brief in articles[3:7] %}
                        <div class="brief-item">
                            <!-- Title is Bold, Snippet is Normal weight -->
                            <a href="{{ brief.link }}" class="brief-title" target="_blank">{{ brief.title }}</a>
                            {% set snip = brief.snippet %}
                            <a href="{{ brief.link }}" class="brief-snippet" target="_blank" style="text-decoration:none; display:block;">{{ snip[:90] ~ '...더보기' if snip|length > 90 else snip }}</a>
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>

            </div>

            <!-- Bottom Corporate CTA -->
            <div class="cta-section">
                <a href="#" class="cta-button" target="_blank">Request a Free Demo</a>
                <a href="#" class="cta-button" target="_blank">Explore Past Issues</a>
                <div class="cta-subtext">
                    This insight report was curated by FOS System Team.<br>
                    For inquiries, contact: {{ sender }}<br>
                    &copy; 2026 FOS INC. All rights reserved.
                </div>
            </div>

        </div>
    </body>
    </html>
    """
    from datetime import datetime
    today_date = datetime.now().strftime('%B %d, %Y')
    
    from jinja2 import Template
    template = Template(template_str)
    return template.render(articles=articles, sender=SMTP_EMAIL, today_date=today_date.upper())


def send_newsletter(recipients, subject, html_content):
    """여러 수신자에게 이메일 발송"""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("이메일 발송 권한이 없습니다 (.env 파일 확인)")
        return False
        
    try:
        # 1. SMTP 서버 연결
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        # 2. 로그인
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        
        # 3. 이메일 구성 및 발송
        for recipient in recipients:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"코다리 뉴스레터 <{SMTP_EMAIL}>"
            msg['To'] = recipient
            
            # HTML 본문 추가
            part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part)
            
            server.send_message(msg)
            print(f"✅ {recipient} 에게 뉴스레터 발송 완료!")
            
        # 4. 종료
        server.quit()
        return True
    except Exception as e:
        print(f"❌ 이메일 발송 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    # Test
    sample_articles = [
         {
            "title": "테스트 기사: 코다리 부장의 업무 자동화 꿀팁",
            "link": "https://example.com",
            "source": "AI 매거진",
            "score": 9,
            "snippet": "업무를 자동화하고 칼퇴하는 방법에 대해 알아봅니다.",
            "thumbnail": ""
        }
    ]
    html = create_email_html(sample_articles)
    # send_newsletter([SMTP_EMAIL], "[테스트] 뉴스레터 발송 테스트", html)
    print("Email HTML Generated Successfully (length: {})".format(len(html)))
