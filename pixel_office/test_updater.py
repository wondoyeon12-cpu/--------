import json
import time
import random
import os

STATUS_FILE = "agent_status.json"

TASKS = [
    "SEO 키워드 리서치 중...",
    "경쟁사 웹페이지 스크래핑",
    "트렌드 분석 시작",
    "랜딩페이지 카피 작성",
    "유튜브 스크립트 작성 중...",
    "코드 디버깅 완료!",
    "커피 마시는 중...",
    "휴식 중",
    "대표님 지시 대기 중...",
    "메일 발송 자동화"
]

def load_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_status(data):
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    print("AI 요원들의 상태를 랜덤하게 업데이트합니다... (중지하려면 Ctrl+C)")
    
    while True:
        data = load_status()
        if not data:
            # 기본 데이터
            data = {
              "글 팀장": {"status": "idle", "task": "대기 중"},
              "영상 팀장": {"status": "idle", "task": "대기 중"},
              "키워드 팀장": {"status": "idle", "task": "대기 중"},
              "코다리 부장": {"status": "idle", "task": "대기 중"}
            }
            
        # 에이전트 한 명 골라서 상태 랜덤 변경
        target = random.choice(list(data.keys()))
        new_status = random.choice(["idle", "working"])
        new_task = "대기 중" if new_status == "idle" else random.choice(TASKS)
        
        data[target]["status"] = new_status
        data[target]["task"] = new_task
        
        print(f"[{target}] 상태 변경 -> {new_status} ({new_task})")
        save_status(data)
        
        # 2초 ~ 5초 사이로 잠듦
        time.sleep(random.uniform(2.0, 5.0))

if __name__ == "__main__":
    main()
