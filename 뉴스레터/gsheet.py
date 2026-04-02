import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets API 연동 범위
SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

# (주의) 구글 시트 ID나 URL
# 권한이 이메일 주소(credentials.json의 client_email)에 부여되어야 함
SPREADSHEET_NAME = "뉴스레터_구독자명단" 
# 또는 URL 사용 가능
# SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/abc..."

def get_subscribers(credentials_file='credentials.json'):
    """Google Sheets 문서에서 구독자 이메일 목록을 읽어옵니다. (1열 가정)"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, SCOPE)
        client = gspread.authorize(creds)
        
        # 파일 이름으로 찾기 (에러나면 URL 사용 권장)
        # sheet = client.open(SPREADSHEET_NAME).sheet1
        
        # (테스트용) 일단 엑셀 연결 대신 더미 데이터 반환
        # FIXME: 실제 구글 시트 문서 생성 및 공유 후 해제
        # records = sheet.get_all_records()
        # return [row['이메일'] for row in records if '이메일' in row]
        
        import os
        return [os.getenv("SMTP_EMAIL")]
    except Exception as e:
        print(f"구글 시트를 읽어오는 중 에러 발생: {e}")
        return []

if __name__ == "__main__":
    subscribers = get_subscribers()
    print("구독자 목록:", subscribers)
