import os
from notion_client import Client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

def save_summary_to_notion(markdown_summary):
    """
    AI가 요약한 마크다운을 노션 데이터베이스의 새 페이지로 저장합니다.
    """
    if not notion:
        print("Notion 토큰이 설정되지 않았습니다.")
        return False

    today_str = datetime.now().strftime("%Y-%m-%d")
    title = f"{today_str} 데일리 슬랙 브리핑"

    # 마크다운 텍스트를 노션 블록(Paragraph)으로 단순 변환
    # (실무에서는 헤딩, 불릿, 체크박스 등 세분화된 파싱이 필요할 수 있지만, 여기선 Text Block으로 분할 처리)
    blocks = []
    lines = markdown_summary.split("\n")
    for line in lines:
        if line.strip() == "":
            continue
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": line}
                    }
                ]
            }
        })

    try:
        new_page = notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties={
                "Name": { # 'Name' 혹은 '이름' 등 DB의 기본 타이틀 속성 이름에 맞춰야 함
                    "title": [
                        {
                            "text": {"content": title}
                        }
                    ]
                }
            },
            children=blocks
        )
        print(f"Notion 페이지가 성공적으로 생성되었습니다: {new_page['url']}")
        return True
    except Exception as e:
        print(f"Notion 업로드 중 오류 발생: {e}")
        return False
