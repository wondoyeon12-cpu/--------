import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_FILEPATH = os.getenv("DB_FILEPATH", "slack_data.db")

def init_db():
    """초기 데이터베이스 및 테이블을 생성합니다."""
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            thread_ts TEXT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 기존 DB에 thread_ts 컬럼 없으면 추가 (무중단 마이그레이션)
    try:
        cursor.execute('ALTER TABLE messages ADD COLUMN thread_ts TEXT DEFAULT NULL')
    except Exception:
        pass  # 이미 컬럼이 있으면 무시
    conn.commit()
    conn.close()

def save_message(channel_id, user_id, text, timestamp, thread_ts=None):
    """새로운 슬랙 메시지를 DB에 저장합니다. thread_ts가 있으면 쓰레드 답글."""
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (channel_id, user_id, text, timestamp, thread_ts)
        VALUES (?, ?, ?, ?, ?)
    ''', (channel_id, user_id, text, timestamp, thread_ts))
    conn.commit()
    conn.close()

def get_recent_messages(channel_id, limit=50):
    """지정된 채널의 최근 메시지를 가져옵니다. (AI 문맥 파악용)"""
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, text, timestamp FROM messages
        WHERE channel_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (channel_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    # 시간 역순으로 가져왔으므로 다시 시간 순으로 정렬 반환
    return list(reversed(rows))

def get_message_by_ts(timestamp):
    """지정된 타임스탬프의 메시지 원본을 가져옵니다."""
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT channel_id, user_id, text, timestamp FROM messages
        WHERE timestamp = ?
        LIMIT 1
    ''', (timestamp,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_replies_by_thread_ts(parent_ts):
    """특정 메시지의 쓰레드 답글 목록을 가져옵니다."""
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, text, timestamp FROM messages
        WHERE thread_ts = ? AND timestamp != ?
        ORDER BY timestamp ASC
    ''', (parent_ts, parent_ts))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_daily_messages():
    """하루 동안의 모든 메시지를 가져옵니다. (일일 요약 생성용) - VIP 채널 제외"""
    VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID", "")
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT channel_id, user_id, text, timestamp FROM messages
        WHERE channel_id != ? AND channel_id != 'wecyd-bot'
        ORDER BY timestamp ASC
    ''', (VIP_CHANNEL_ID,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def clear_old_messages():
    """DB에 쌓인 모든 메시지를 비웁니다. (요약 완료 후 호출) -> 7일 지난 메시지 삭제로 변경"""
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE created_at <= datetime('now', '-7 days')")
    conn.commit()
    conn.close()

def get_filtered_messages(start_ts: str, end_ts: str, target_channel_id: str = None):
    """지정된 기간, 채널 조건에 맞는 메시지를 가져옵니다."""
    VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID", "")
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    
    query = '''
        SELECT channel_id, user_id, text, timestamp FROM messages
        WHERE channel_id != ? AND channel_id != 'wecyd-bot'
        AND timestamp >= ? AND timestamp <= ?
    '''
    params = [VIP_CHANNEL_ID, start_ts, end_ts]
        
    if target_channel_id:
        query += " AND channel_id = ?"
        params.append(target_channel_id)
        
    query += " ORDER BY timestamp ASC"
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows

# 스크립트가 직접 실행될 때 DB 초기화
if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_FILEPATH}")
