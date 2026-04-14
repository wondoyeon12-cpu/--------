import sqlite3
import time
import os

def insert_dummy_data():
    db_path = os.path.join(os.path.dirname(__file__), 'slack_data.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    now_ts = time.time()
    
    # 10 dummy channels
    channels = [
        "마케팅팀", "디자인팀", "영업기획", "개발팀", "인사팀",
        "경영지원", "CS팀", "전략기획팀", "재무팀", "콘텐츠운영팀"
    ]
    
    data = []
    
    messages = {
        "마케팅팀": ["관절보궁 봄 프로모션 어제 성과 공유합니다.", "클릭률이 15% 상승했습니다.", "추가 예산 배정 요청드립니다."],
        "디자인팀": ["메인 배너 시안 A, B팀 공유드렸습니다.", "B안이 더 깔끔해 보이네요.", "폰트 크기를 조금 더 키웠습니다."],
        "영업기획": ["재고 5000개 입고 완료되었습니다.", "물류센터 쪽에 출고 지연 없는지 체크 부탁드립니다.", "문제 없습니다."],
        "개발팀": ["결제 모듈 연동 버그 픽스 완료했습니다.", "QA팀 테스트 부탁드립니다.", "안드로이드 앱 크래시 리포트 확인중입니다."],
        "인사팀": ["상반기 워크샵 일정 투표 올려드렸습니다.", "장소 섭외는 어디까지 진행되었나요?", "이번주 내로 3곳 추려서 보고하겠습니다."],
        "경영지원": ["이번달 법인카드 사용 내역 제출 내일까지입니다.", "영수증 누락되신 분들 확인해주세요.", "확인했습니다."],
        "CS팀": ["당일 배송 문의가 급증하고 있습니다.", "FAQ 팝업 띄우면 어떨까요?", "홈페이지 메인에 공지 올리겠습니다."],
        "전략기획팀": ["경쟁사 신제품 런칭 리포트 첨부합니다.", "가격 포지셔닝이 좀 공격적이네요.", "저희도 대응 방안 마련하겠습니다."],
        "재무팀": ["1분기 결산 보고서 초안 완성되었습니다.", "영업이익이 예상보다 높네요.", "마케팅 비용 최적화 덕분인 것 같습니다."],
        "콘텐츠운영팀": ["유튜브 숏츠 대본 작성 끝났습니다.", "썸네일 방향성 논의하시죠.", "어그로성 제목 한두개 뽑아주세요."]
    }
    
    for i, channel in enumerate(channels):
        for j, msg in enumerate(messages[channel]):
            # U_DUMMY prefix ensures easy cleanup
            user_id = f"<@U_DUMMY_{i}_{j}>"
            ts = now_ts - (600 * i) - (60 * j) # Spread within recent hours
            data.append((channel, user_id, msg, ts))
            
    for channel_id, user_id, text, timestamp in data:
        cursor.execute('''
            INSERT INTO messages (channel_id, user_id, text, timestamp, thread_ts)
            VALUES (?, ?, ?, ?, ?)
        ''', (channel_id, user_id, text, str(timestamp), str(timestamp)))

    conn.commit()
    conn.close()
    print("Dummy data for 10 channels has been successfully inserted!")

if __name__ == '__main__':
    insert_dummy_data()
