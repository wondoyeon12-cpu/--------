import os
import sys
import argparse
import requests
import base64
from bs4 import BeautifulSoup, Comment

# Force UTF-8 encoding for standard output
sys.stdout.reconfigure(encoding='utf-8')

WP_URL = 'https://dailywell.co.kr'
from dotenv import load_dotenv
load_dotenv()

USERNAME = os.getenv('WP_USERNAME', 'wondoyeon12@gmail.com')
PASSWORD = os.getenv('WP_PASSWORD', '')
API_ENDPOINT = f"{WP_URL}/wp-json/wp/v2"

credentials = f"{USERNAME}:{PASSWORD}"
token = base64.b64encode(credentials.encode()).decode('utf-8')
auth_header = {'Authorization': f'Basic {token}'}

def upload_media(image_path):
    if not os.path.exists(image_path):
        print(f"❌ 이미지를 찾을 수 없습니다: {image_path}")
        return None
    
    filename = os.path.basename(image_path)
    with open(image_path, 'rb') as img:
        media_data = img.read()
        
    headers = {
        'Authorization': auth_header['Authorization'],
        'Content-Type': 'image/png', # Can be dynamically detected, but using png as fallback is generally ok for WP
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    
    print(f"🔄 이미지 업로드 중: {filename}...")
    response = requests.post(f"{API_ENDPOINT}/media", headers=headers, data=media_data)
    
    if response.status_code == 201:
        wp_url = response.json()['source_url']
        print(f"✅ 이미지 업로드 완료: {wp_url}")
        return wp_url
    else:
        print(f"❌ 이미지 업로드 실패 ({response.status_code}): {response.text}")
        return None

def create_post(title, content, save_as_draft=True):
    status = 'draft' if save_as_draft else 'publish'
    post = {
        'title': title,
        'status': status,
        'content': content
    }
    headers = {
        'Authorization': auth_header['Authorization'],
        'Content-Type': 'application/json'
    }
    
    print(f"📝 게시글 생성 중 (상태: {status})...")
    response = requests.post(f"{API_ENDPOINT}/posts", headers=headers, json=post)
    
    if response.status_code == 201:
        link = response.json()['link']
        post_id = response.json()['id']
        print(f"✅ 워드프레스 업로드 성공! (ID: {post_id})")
        print(f"🔗 링크: {link}")
        return link
    else:
        print(f"❌ 게시글 생성 실패 ({response.status_code}): {response.text}")
        return None

def process_and_upload(file_path, save_as_draft=True):
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return
        
    print(f"\n🚀 문서 처리 시작: {file_path}")
    base_dir = os.path.dirname(os.path.abspath(file_path))
    
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
    # Remove HTML comments to avoid WP block issues
    for comments in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comments.extract()
        
    # Extract Title from h1 or .main-title
    title_tag = soup.find('h1')
    if not title_tag:
        title_tag = soup.find(class_='main-title')
    title = title_tag.text.strip() if title_tag else "제목 없음 (시스템 자동 생성)"
    
    # Try finding container or body
    container = soup.find(class_='kodari-article-box')
    if not container:
        container = soup.find('body')
        
    if not container:
        # Wrap everything if no body or container
        container = BeautifulSoup("<body>" + str(soup) + "</body>", 'html.parser').find('body')
        
    # Remove H1 from body if it exists to avoid duplication in WP
    h1_in_container = container.find('h1')
    if h1_in_container:
        h1_in_container.decompose()
        
    style = soup.find('style')
    
    # Upload and replace images
    for img in container.find_all('img'):
        src = img.get('src')
        if src and not src.startswith('http'):
            # Resolve path relative to html file
            local_img_path = os.path.normpath(os.path.join(base_dir, src))
            wp_url = upload_media(local_img_path)
            if wp_url:
                img['src'] = wp_url
                
    inner_html = ''.join(str(child) for child in container.children)
    style_str = str(style) if style else ''
    
    # Check if content is already wrapped with a styling container
    if 'kodari-article-box' in str(container) or 'article-container' in str(container):
        final_html = f"<!-- wp:html -->\n{style_str}\n{inner_html}\n<!-- /wp:html -->"
    else:
        final_html = f"""<!-- wp:html -->
<div class="article-container" style="max-width: 800px; margin: 0 auto; padding: 30px; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 15px; box-sizing: border-box;">
    {style_str}
    {inner_html}
</div>
<!-- /wp:html -->"""

    create_post(title, final_html, save_as_draft=save_as_draft)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="워드프레스 자동 업로드 스크립트 (코다리 부장 🐟)")
    parser.add_argument("files", nargs="*", help="업로드할 HTML 파일 경로(들)")
    parser.add_argument("--publish", action="store_true", help="임시글이 아닌 바로 발행 상태로 업로드")
    args = parser.parse_args()
    
    if not args.files:
        print("💡 사용법: python wp_auto_upload.py [파일명1.html] [파일명2.html] ...")
        print("💡 예시: python wp_auto_upload.py article_parkgolf.html --publish")
    else:
        save_as_draft = not args.publish
        for f in args.files:
            process_and_upload(f, save_as_draft=save_as_draft)
