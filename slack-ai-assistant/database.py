import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# database.py 파일이 있는 디렉토리를 기준으로 절대 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILEPATH = os.path.join(BASE_DIR, os.getenv("DB_FILEPATH", "slack_data.db"))

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
    
    # 브리핑 실행 로그 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS briefing_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            briefing_type TEXT NOT NULL, -- 'morning' or 'afternoon'
            run_date TEXT NOT NULL,      -- 'YYYY-MM-DD'
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

def get_daily_messages(start_ts=None):
    """지정된 시점(start_ts)부터 현재까지의 모든 메시지를 가져옵니다. (일일 요약 생성용) - VIP 채널 제외"""
    VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID", "")
    
    if start_ts is None:
        # 시점이 지정되지 않으면 기본적으로 어제 00:00:00부터 가져옴
        import datetime
        now = datetime.datetime.now()
        yesterday_zero = (now - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        start_ts = str(yesterday_zero.timestamp())

    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT channel_id, user_id, text, timestamp FROM messages
        WHERE channel_id != ? AND channel_id != 'wecyd-bot'
        AND CAST(timestamp AS REAL) >= ?
        ORDER BY timestamp ASC
    ''', (VIP_CHANNEL_ID, start_ts))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_last_briefing_time(briefing_type):
    """특정 타입의 마지막 브리핑 성공 시간을 Unix Timestamp로 가져옵니다."""
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    # strftime('%s', created_at) 는 SQLite에서 Unix timestamp를 반환함
    cursor.execute('''
        SELECT strftime('%s', created_at) FROM briefing_logs 
        WHERE briefing_type = ? 
        ORDER BY created_at DESC LIMIT 1
    ''', (briefing_type,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_last_message_timestamp():
    """DB에 저장된 가장 최신 메시지의 타임스탬프를 가져옵니다. (부재중 메시지 백필용)"""
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp FROM messages ORDER BY timestamp DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def clear_old_messages():
    """DB에 쌓인 모든 메시지를 비웁니다. (요약 완료 후 호출) -> 7일 지난 메시지 삭제로 변경"""
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE created_at <= datetime('now', '-7 days')")
    conn.commit()
    conn.close()

def get_filtered_messages(start_ts: str = None, end_ts: str = None, target_channel_id: str = None):
    """지정된 기간, 채널 조건에 맞는 메시지를 가져옵니다."""
    VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID", "")
    
    if start_ts is None:
        # 기본값: 오늘 00:00:00
        start_ts = str(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    
    if end_ts is None:
        # 기본값: 현재 시간
        end_ts = str(datetime.now().timestamp())

    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    
    query = '''
        SELECT channel_id, user_id, text, timestamp FROM messages
        WHERE channel_id != ? AND channel_id != 'wecyd-bot'
        AND CAST(timestamp AS REAL) >= ? AND CAST(timestamp AS REAL) <= ?
    '''
    params = [VIP_CHANNEL_ID, start_ts, end_ts]
        
    if target_channel_id:
        import re
        def normalize_name(name):
            if not name: return ""
            name = re.sub(r'[\s\-_]', '', name)
            for suffix in ['채널', '팀', '방']:
                if name.endswith(suffix):
                    name = name[:-len(suffix)]
            return name.lower()

        target_norm = normalize_name(target_channel_id)
        
        cursor.execute("SELECT DISTINCT channel_id FROM messages")
        all_channels = [r[0] for r in cursor.fetchall() if r[0]]
        
        matched_channels = []
        for c in all_channels:
            c_norm = normalize_name(c)
            if c_norm and target_norm:
                if c_norm == target_norm or target_norm in c_norm or c_norm in target_norm:
                    matched_channels.append(c)
                    
        if matched_channels:
            placeholders = ','.join(['?'] * len(matched_channels))
            query += f" AND channel_id IN ({placeholders})"
            params.extend(matched_channels)
        else:
            query += " AND channel_id = ?"
            params.append(target_channel_id)
        
    query += " ORDER BY timestamp ASC"
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows

def is_briefing_sent_today(briefing_type):
    """오늘 해당 타입의 브리핑이 이미 발송되었는지 확인합니다."""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM briefing_logs WHERE briefing_type = ? AND run_date = ?', (briefing_type, today))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def log_briefing_sent(briefing_type):
    """오늘 해당 타입의 브리핑이 발송되었음을 기록합니다."""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_FILEPATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO briefing_logs (briefing_type, run_date) VALUES (?, ?)', (briefing_type, today))
    conn.commit()
    conn.close()

# 스크립트가 직접 실행될 때 DB 초기화
if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_FILEPATH}")
