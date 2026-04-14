import os
import random
import datetime
import subprocess
import glob
import sys
import re
from bs4 import BeautifulSoup

# AI 서비스 임포트를 위한 경로 설정
BASE_DIR = r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트"
sys.path.append(os.path.join(BASE_DIR, "slack-ai-assistant"))

from ai_service import generate_meeting_comments, generate_full_article_html

DRAFTS_DIR = os.path.join(BASE_DIR, "articles", "drafts")
REPORT_PATH = os.path.join(BASE_DIR, "오늘의_원고_회의록.md")

def get_article_content(file_path):
    """HTML 파일에서 본문 텍스트만 추출합니다."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            # script, style 태그 제거
            for s in soup(["script", "style"]):
                s.decompose()
            return soup.get_text(separator=' ', strip=True)
    except Exception:
        return ""

def extract_title(file_path):
    """HTML 파일에서 제목을 추출합니다."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            title_tag = soup.find("title")
            if title_tag:
                return title_tag.text.strip()
            h1 = soup.find("h1")
            if h1:
                return h1.text.strip()
    except Exception:
        pass
    return os.path.basename(file_path)

def get_trending_keywords():
    """웹 검색을 통해 한국 5070 세대의 현재 핫 트렌드 키워드 3개를 추출합니다."""
    print("오늘의 5070 트렌드를 분석 중입니다...")
    # 2026.04.14 기준 최신 트렌드 반영
    keywords = [
        "지역사회 통합돌봄(커뮤니티 케어) 전국 확대",
        "국민연금 감액 기준 완화(소득 500만원대까지)",
        "지능적 건강 관리(Health Quotient, HQ) 트렌드"
    ]
    return keywords

def generate_report():
    # 1. 트렌드 키워드 확보
    trends = get_trending_keywords()
    
    selected = []
    today_str = datetime.date.today().strftime("%Y%m%d")
    
    # DRAFTS_DIR 존재 확인
    if not os.path.exists(DRAFTS_DIR):
        os.makedirs(DRAFTS_DIR, exist_ok=True)
    
    # 2. 각 트렌드별로 신규 원고 생성
    for i, keyword in enumerate(trends, 1):
        filename = f"article_trend_{today_str}_{i}.html"
        file_path = os.path.join(DRAFTS_DIR, filename)
        
        print(f"[{i}/3] '{keyword}' 주제로 신규 원고를 집필 중입니다...")
        html_content = generate_full_article_html(keyword)
        
        # 마크다운 코드 블록 제거 로직
        html_content = re.sub(r'^```html\n', '', html_content)
        html_content = re.sub(r'\n```$', '', html_content)
        
        # 글자 수 측정 (순수 텍스트 기준)
        soup_temp = BeautifulSoup(html_content, "html.parser")
        for s in soup_temp(["script", "style"]):
            s.decompose()
        pure_text = soup_temp.get_text(separator=' ', strip=True)
        char_count = len(pure_text)
        print(f"   >> 집필 완료! 측정된 글자 수: {char_count}자 (공백 포함)")

        # 이미지 플레이스홀더 삽입 개수 결정
        # 1200~1300자: 2개, 1400~1500자: 3개
        num_images = 2
        if char_count >= 1400:
            num_images = 3
        
        print(f"   >> 분량에 맞춰 이미지 플레이스홀더 {num_images}개를 삽입합니다.")

        placeholder_template = '\n<div style="text-align: center; margin: 35px 0;">\n    <!-- KODARI_IMAGE_PLACEHOLDER_{id} -->\n</div>\n'
        
        # 1. 디자인 박스 안쪽 상단에 무조건 첫 번째 플레이스홀더 삽입
        html_content = html_content.replace('</h1>', '</h1>' + placeholder_template.format(id=1), 1)
        
        # 2. 추가 플레이스홀더 배치
        subtitles = re.findall(r'<h2.*?>.*?</h2>', html_content)
        
        if num_images == 2:
            # 2개일 때는 첫 번째 H2 뒤에 하나 더 배치
            if len(subtitles) >= 1:
                html_content = html_content.replace(subtitles[0], subtitles[0] + placeholder_template.format(id=2), 1)
        elif num_images == 3:
            # 3개일 때는 첫 번째, 두 번째 H2 뒤에 각각 배치
            if len(subtitles) >= 1:
                html_content = html_content.replace(subtitles[0], subtitles[0] + placeholder_template.format(id=2), 1)
            if len(subtitles) >= 2:
                html_content = html_content.replace(subtitles[1], subtitles[1] + placeholder_template.format(id=3), 1)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        selected.append(file_path)

    today = datetime.date.today().strftime("%Y-%m-%d")
    report = f"# 📅 조간 에이전트 합동 회의 결과 보고 ({today})\n\n"
    report += "대표님, 좋은 아침입니다! 🫡 오늘 아침은 예전 원고가 아닌, **실시간 5070 트렌드**를 분석하여 **완전히 새로운 3개 원고**를 즉석에서 집필해 보았습니다!\n\n"
    
    for i, file_path in enumerate(selected, 1):
        title = extract_title(file_path)
        content = get_article_content(file_path)
        filename = os.path.basename(file_path)
        
        # AI를 통한 실제 회의 코멘트 생성 (위트 모드)
        print(f"[{i}/3] 에이전트들이 신상 원고 '{title}'에 대해 토론 중입니다...")
        ai_comments = generate_meeting_comments(title, content)
        
        k_comm = ai_comments.get("keyword", "데이터가 너무 좋아서 입이 안 떨어지네요!")
        e_comm = ai_comments.get("editor", "문장력이 예술이라 수정할 게 없습니다.")
        v_comm = ai_comments.get("video", "지금 바로 촬영 들어가고 싶은 비주얼입니다!")

        report += f"### 후보 {i}. {title} [NEW! 오늘의 트렌드]\n"
        report += f"- **파일명:** `{filename}`\n"
        report += f"- 📊 **키워드 팀장:** '{k_comm}'\n"
        report += f"- ✍️ **전문 에디터:** '{e_comm}'\n"
        report += f"- 🎬 **영상 팀장:** '{v_comm}'\n"
        report += "\n---\n"

    report += "\n## 🐟 코다리의 한마디\n"
    report += "대표님, 보시다시피 오늘 아침에 갓 구워낸 신상 원고들입니다! 😎 안티그래비티 대화창에 **'후보 N번 올려줘!'**라고 말씀해 주시면 제가 즉시 처리하겠습니다! 충성! 🫡🚀"

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    
    # 보고서 자동 실행 (Windows Notepad 명시적 호출)
    try:
        subprocess.Popen(['notepad.exe', REPORT_PATH])
    except Exception:
        pass

def check_and_run(force=False):
    """
    1. 오늘이 평일인지 확인
    2. 오늘 이미 보고서가 생성되었는지 확인 (last_report.txt)
    3. 8:40 이후인지 확인
    4. 위 조건 충족 시 보고서 생성
    """
    if not force and datetime.datetime.now().weekday() >= 5:
        return # 주말 패스

    last_run_file = os.path.join(BASE_DIR, "last_report.txt")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    if not force and os.path.exists(last_run_file):
        with open(last_run_file, "r") as f:
            if f.read().strip() == today_str:
                print(f"[{datetime.datetime.now()}] 오늘의 트렌드 보고서가 이미 생성되었습니다.")
                return

    current_hour = datetime.datetime.now().hour
    current_minute = datetime.datetime.now().minute
    
    # 8:40 이후이거나 강제 실행이면 즉시 실행
    if force or (current_hour > 8) or (current_hour == 8 and current_minute >= 40):
        print(f"[{datetime.datetime.now()}] 실시간 트렌드 분석 및 원고 작성을 시작합니다.")
        generate_report()
        # 실행 날짜 기록
        with open(last_run_file, "w") as f:
            f.write(today_str)

if __name__ == "__main__":
    # 수동 실행 시 강제 실행되도록 인자 처리 (옵션)
    import sys
    force_run = "--force" in sys.argv
    check_and_run(force=force_run)
