import sqlite3
import time
import os

db_path = os.path.join(os.path.dirname(__file__), 'slack_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
now_ts = time.time()

messages = [
    "이번 주 영업기획팀 주간 회의는 오후 2시입니다.",
    "네 확인했습니다.",
    "B2B 제휴 관련해서 C사 담당자 연락처 아시는 분?",
    "제가 슬랙 DM으로 보내드릴게요.",
    "내일 홈쇼핑 미팅 자료 초안 좀 리뷰해주실 수 있나요?",
    "지금은 외근 중이라 복귀해서 4시쯤 보겠습니다.",
    "오프라인 매장 입점 관련해서 수수료 협의는 어떻게 되었나요?",
    "현재 15%에서 13%로 낮추는 방향으로 논의 중입니다.",
    "재고 부족 이슈가 잦네요. 수요 예측 모델 한번 갈아엎어야 하지 않을까 싶습니다.",
    "공감합니다. 지난달 데이터 뽑아보고 이번주 금요일에 랩업해보죠.",
    "관절보궁 홈쇼핑 편성 시간대가 확정되었습니다! 토요일 오전 7시입니다.",
    "오전 7시면 타겟층 시청률이 아주 높은 시간대네요! 고생하셨습니다.",
    "이 시간대면 준비 물량 10,000세트는 무조건 넘기겠네요.",
    "저번에 런칭했던 프로모션 A/B 테스트 결과 나왔나요?",
    "네, A안이 전환율이 2.5% 더 높았습니다. 보고서 문서 첨부할게요.",
    "확인했습니다. B안은 드랍하고 A안으로 全매체 확대 적용하시죠.",
    "이번 달 팀 회식 어떻게 할까요? 장소 추천 받습니다.",
    "저번에 갔던 소고기집이 좋았는데 예약 빡세겠죠?",
    "제가 한번 전화해보겠습니다.",
    "대표님 지시사항으로 이번 분기 유통 마진율 재검토가 필요합니다.",
    "아, 마진율... 빡세네요. 물류비 인상이 제일 큰 원인인가요?",
    "네, 맞습니다. 택배사 계약 조건 단가 인상 건 때문에 타격이 있네요.",
    "물류센터 쪽에 재계약 조건 다시 한번 협의해볼 여지가 있을까요?",
    "내일 물류팀장님이랑 미팅 잡아보겠습니다.",
    "오늘까지 파트너사 세일즈 키트 배포 완료되어야 합니다.",
    "지금 90% 정도 대리점엔 다 발송되었습니다.",
    "나머지 10%는 주소지 오류 건이라 확인 후 내일 오전 중으로 마무리하겠습니다.",
    "고생 많으십니다.",
    "혹시 작년 추석 기획전 성과 데이터 갖고 계신 분?",
    "아카이브 폴더(영업_2025_Q3)에 엑셀로 정리되어 있습니다.",
    "찾았습니다. 감사합니다!",
    "이번 신규 패키징 단가 협상 건, 공장이랑 어느 정도 얘기 되었나요?",
    "수량 5만개 게런티 조건으로 단가 150원까지 맞췄습니다.",
    "오! 훌륭하네요. 150원이면 마진율 개선에 크게 도움 되겠습니다.",
    "계약서 초안 법무팀 검토 올리겠습니다.",
    "다들 오늘 하루도 파이팅입니다!"
]

data = []
for idx, msg in enumerate(messages):
    user_id = f"<@U_DUMMY_SALES_{idx}>"
    ts = now_ts - 3600 + (idx * 60) # Spread out linearly within the last hour
    data.append(("영업기획", user_id, msg, ts))

for channel_id, user_id, text, timestamp in data:
    cursor.execute('''
        INSERT INTO messages (channel_id, user_id, text, timestamp, thread_ts)
        VALUES (?, ?, ?, ?, ?)
    ''', (channel_id, user_id, text, str(timestamp), str(timestamp)))

conn.commit()
conn.close()
print("30+ dummy messages for 영업기획 have been successfully inserted!")
