import os
import sys
import requests
import base64
from bs4 import BeautifulSoup, Comment

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
        print(f"❌ File not found: {image_path}")
        return None
    
    filename = os.path.basename(image_path)
    with open(image_path, 'rb') as img:
        media_data = img.read()
        
    headers = {
        'Authorization': auth_header['Authorization'],
        'Content-Type': 'image/png',
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    
    print(f"Uploading image: {filename}...")
    response = requests.post(f"{API_ENDPOINT}/media", headers=headers, data=media_data)
    
    if response.status_code == 201:
        return response.json()['source_url']
    else:
        print(f"❌ Media upload failed: {response.status_code} - {response.text}")
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
    response = requests.post(f"{API_ENDPOINT}/posts", headers=headers, json=post)
    if response.status_code == 201:
        return response.json()['link']
    else:
        print(f"❌ Post creation failed: {response.status_code} - {response.text}")
        return None

files = [
    r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트\article_implant.html"
]

for file_path in files:
    print(f"Processing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
        # Remove HTML comments to avoid showing prompts in editor
        for comments in soup.findAll(string=lambda text: isinstance(text, Comment)):
            comments.extract()
            
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "제목 없음"
        
        body = soup.find('body')
        if not body:
            # HTML 구조에 따라 <body> 태그가 없을 수도 있으니, 이런 경우 전체를 컨텐츠로 사용
            print("Wrap with body tag")
            body = BeautifulSoup("<body>" + str(soup) + "</body>", 'html.parser').find('body')
            
        style = soup.find('style')
        
        if body:
            h1_tag = body.find('h1')
            if h1_tag:
                h1_tag.decompose()
                
            # Upload images to WP and replace local src with remote url
            for img in body.find_all('img'):
                src = img.get('src')
                # Check if it's a local file path
                if src and os.path.exists(src):
                    wp_url = upload_media(src)
                    if wp_url:
                        img['src'] = wp_url
                        print(f"✅ Image replaced with WP URL: {wp_url}")
            
            inner_html = ''.join(str(child) for child in body.children)
            # 워드프레스 클래식 블록 방지(wp:html) 및 콘텐츠 영역 박스(article-container) 강제 적용
            wrapped_content = f"""<!-- wp:html -->
<div class="article-container" style="max-width: 800px; margin: 0 auto; padding: 30px; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); box-sizing: border-box;">
    {(str(style) if style else '')}
    {inner_html}
</div>
<!-- /wp:html -->"""
            link = create_post(title, wrapped_content)
            print(f"✅ Uploaded [DRAFT]: {title}")
            print(f"🔗 Link: {link}\n")
        else:
            print(f"❌ Failed to parse body in {file_path}")
