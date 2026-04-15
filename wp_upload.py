import importlib
import sys
import requests
import json
import os
import base64

# Force UTF-8 encoding for standard output to avoid UnicodeEncodeError in Windows console
sys.stdout.reconfigure(encoding='utf-8')

from bs4 import BeautifulSoup

# 워드프레스 접속 정보
WP_URL = 'https://dailywell.co.kr'
from dotenv import load_dotenv
load_dotenv()

USERNAME = os.getenv('WP_USERNAME', 'wondoyeon12@gmail.com')
PASSWORD = os.getenv('WP_PASSWORD', '')
API_ENDPOINT = f"{WP_URL}/wp-json/wp/v2"

# 인증 설정
credentials = f"{USERNAME}:{PASSWORD}"
token = base64.b64encode(credentials.encode()).decode('utf-8')
auth_header = {'Authorization': f'Basic {token}'}

def upload_image(image_path):
    print(f"이미지 업로드 시도 중: {image_path}")
    if not os.path.exists(image_path):
        print(f"❌ 파일을 찾을 수 없습니다: {image_path}")
        return None
        
    filename = os.path.basename(image_path)
    
    with open(image_path, 'rb') as img:
        media_data = img.read()
        
    headers = {
        'Authorization': auth_header['Authorization'],
        'Content-Type': 'image/png', # 기본적으로 png로 가정
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    
    response = requests.post(f"{API_ENDPOINT}/media", headers=headers, data=media_data)
    
    if response.status_code == 201:
        print(f"✅ 이미지 업로드 성공: {filename}")
        return response.json()['source_url']
    else:
        print(f"❌ 이미지 업로드 실패. 상태 코드: {response.status_code}")
        print(response.text)
        return None

def create_post(title, content, save_as_draft=True):
    status = 'draft' if save_as_draft else 'publish'
    print(f"게시글 생성 시도 중 (상태: {status})...")
    
    post = {
        'title': title,
        'status': status,
        'content': content
    }
    
    headers = {
        'Authorization': auth_header['Authorization'],
        'Content-Type': 'application/json'
    }
    
    response = requests.post(f"{API_ENDPOINT}/posts", headers=headers, json=post)
    
    if response.status_code == 201:
        post_id = response.json()['id']
        post_link = response.json()['link']
        print(f"✅ 게시글 생성 성공! ID: {post_id}")
        print(f"🔗 임시저장 링크: {post_link}")
        return True
    else:
        print(f"❌ 게시글 생성 실패. 상태 코드: {response.status_code}")
        print(response.text)
        return False

def main():
    # 1. HTML 파일 읽기
    BASE_DIR = r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트"
    # 업로드할 파일 경로 설정 (새로운 기사 파일로 변경)
    html_path = os.path.join(BASE_DIR, "article_naengi.html")
    print(f"📄 HTML 파일 읽는 중: {html_path}")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
    # 제목 추출 (main-title 클래스)
    title_tag = soup.find(class_='main-title')
    title = title_tag.text.strip() if title_tag else "제목 없음 (시스템 자동 생성)"
    
    # 본문 추출 (kodari-article-box 내부)
    # 제목 태그는 본문에서 제거하거나 남겨두거나 선택 가능. 여기서는 남겨둠.
    container = soup.find(class_='kodari-article-box')
    if not container:
         print("❌ kodari-article-box 클래스를 찾을 수 없습니다.")
         return
         
    # 2. 이미지 업로드 및 URL 교체
    images = container.find_all('img')
    for img in images:
        src = img.get('src')
        if src and src.startswith('./images/'):
            # 로컬 경로 구성
            local_img_path = os.path.join(BASE_DIR, src.replace('./', ''))
            
            # 워드프레스에 업로드
            wp_image_url = upload_image(local_img_path)
            
            if wp_image_url:
                 # HTML 내 src 변경
                 img['src'] = wp_image_url
                 print(f"🔄 이미지 src 교체 완료: {wp_image_url}")

    # 최종 HTML 문자열 추출
    # 스타일 태그(CSS)를 포함해야 워드프레스에서도 가독성과 너비 설정이 유지됩니다.
    style_tag = soup.find('style')
    style_str = str(style_tag) if style_tag else ""
    final_html = style_str + "\n" + str(container)
    
    # 3. 새 글 발행
    create_post(title, final_html, save_as_draft=True)

if __name__ == "__main__":
    main()
