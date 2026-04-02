import os
import sys
import requests
import base64
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

WP_URL = 'https://dailywell.co.kr'
USERNAME = 'wondoyeon12@gmail.com'
PASSWORD = 'gC13 1hW4 bG5w J2RH IhsN di4L'
API_ENDPOINT = f"{WP_URL}/wp-json/wp/v2"

credentials = f"{USERNAME}:{PASSWORD}"
token = base64.b64encode(credentials.encode()).decode('utf-8')
auth_header = {'Authorization': f'Basic {token}'}

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
        print(f"Error: {response.status_code} - {response.text}")
        return None

files = [
    r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트\article_spring_greens_toxicity.html",
    r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트\article_hidden_money.html",
    r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트\article_parkgolf_survival.html"
]

for file_path in files:
    print(f"Processing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else "제목 없음"
        
        body = soup.find('body')
        style = soup.find('style')
        
        if body:
            h1_tag = body.find('h1')
            if h1_tag:
                h1_tag.decompose()
            
            content = (str(style) if style else '') + ''.join(str(child) for child in body.children)
            link = create_post(title, content)
            print(f"✅ Uploaded [DRAFT]: {title}")
            print(f"🔗 Link: {link}\n")
        else:
            print(f"❌ Failed to parse body in {file_path}")
