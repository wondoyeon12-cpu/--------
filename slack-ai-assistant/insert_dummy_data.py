import sqlite3
import time

def insert_dummy_data():
    conn = sqlite3.connect('slack_data.db')
    cursor = conn.cursor()

    # Get current time
    now_ts = time.time()
    
    # Generate some realistic dummy messages for marketing campaign "관절보궁"
    # We will spread them out over the last few hours
    
    data = [
        # Channel: 마케팅팀
        ("마케팅팀", "<@U09CXFRKMHU>", "팀장님, 관절보궁 3월 봄맞이 프로모션 기획안 초안 공유드립니다. 확인 부탁드려요.", now_ts - 7200),
        ("마케팅팀", "<@U12345678>", "네, 방금 확인했습니다. 타겟 광고 매체를 유튜브랑 당근마켓으로 좁힌 건 좋은데, 예산 분배 비율은 어떻게 되나요?", now_ts - 7000),
        ("마케팅팀", "<@U09CXFRKMHU>", "유튜브 70%, 당근마켓 30%로 잡았습니다. 시니어 타겟이라 당근마켓 효율이 좋았다는 지난번 데이터 참고했습니다.", now_ts - 6900),
        ("마케팅팀", "<@U87654321>", "추가로, 상세페이지 상단에 들어갈 카피라이트는 이번 주 금요일까지 픽스하면 될까요?", now_ts - 6800),
        ("마케팅팀", "<@U09CXFRKMHU>", "네, 카피는 일정대로 진행해주시고 A/B 테스트용으로 2가지 버전 준비 부탁드립니다.", now_ts - 6700),
        
        # Channel: 디자인팀
        ("디자인팀", "<@U87654321>", "관절보궁 신규 랜딩페이지 디자인 기획안에 들어갈 메인 이미지 시안 작업 시작했습니다. 모델 이미지 위주로 갈지 원물(성분) 강조 위주로 갈지 의견 부탁드립니다.", now_ts - 3600),
        ("디자인팀", "<@U12345678>", "시니어 타겟인 만큼 신뢰감을 주는 모델 컷을 크게 배치하고, 성분 아이콘은 하단에 작게 나열하는게 클릭률이 좋을 것 같아요.", now_ts - 3500),
        ("디자인팀", "<@U87654321>", "알겠습니다! 모델 컷 위주로 오늘 퇴근 전까지 시안 3종 뽑아서 공유드리겠습니다. 폰트 크기도 시니어 맞춤으로 키울게요.", now_ts - 3400),
        
        # Channel: 영업기획
        ("영업기획", "<@U99999999>", "관절보궁 재고 현황 공유합니다. 현재 물류센터에 5,000세트 보유 중입니다. 봄맞이 프로모션 물량으로 충분할까요?", now_ts - 1800),
        ("영업기획", "<@U09CXFRKMHU>", "지난 명절 특수 때 3,000세트가 나갔으니, 평달 대비 공격적으로 마케팅하면 5,000세트 타이트할 수도 있습니다. 생산 일정 확인 한번 부탁드려요.", now_ts - 1700),
        ("영업기획", "<@U99999999>", "네, 공장 쪽에 이번주 내로 추가 생산 2,000세트 가능한지 확인해보겠습니다. 오후에 다시 보고드릴게요.", now_ts - 1600),
        
        # Channel: 마케팅팀 (New conversation thread about review events)
        ("마케팅팀", "<@U87654321>", "관절보궁 구매 후기 이벤트 경품은 저번처럼 상품권으로 갈까요, 아니면 본품 추가 증정으로 갈까요?", now_ts - 900),
        ("마케팅팀", "<@U12345678>", "아무래도 연령대가 높으신 분들이라 복잡한 상품권보다는 직관적인 **'본품 1+1 기회'** 또는 사은품 증정이 반응이 더 폭발적입니다.", now_ts - 800),
        ("마케팅팀", "<@U09CXFRKMHU>", "그럼 후기 이벤트는 '사진 리뷰 작성 시 관절보궁 1박스 추가 증정(추첨 100명)'으로 픽스하시죠. 이벤트 배너 제작 요청 넣어주세요.", now_ts - 700),
        
        # Recent
        ("마케팅팀", "<@U09CXFRKMHU>", "오늘까지 논의된 관절보궁 마케팅 현황 랩업합니다.\n1. 매체: 유튜브/당근마켓 (7:3)\n2. 디자인: 시니어 타겟 폰트업, 모델 중심 메인 컷\n3. 프로모션: 리뷰 시 본품 증정\n다들 수고 많으셨습니다!", now_ts - 100)
    ]
    
    for channel_id, user_id, text, timestamp in data:
        cursor.execute('''
            INSERT INTO messages (channel_id, user_id, text, timestamp, thread_ts)
            VALUES (?, ?, ?, ?, ?)
        ''', (channel_id, user_id, text, str(timestamp), str(timestamp)))

    conn.commit()
    conn.close()
    print("Dummy data for '관절보궁' has been successfully inserted!")

if __name__ == '__main__':
    insert_dummy_data()
