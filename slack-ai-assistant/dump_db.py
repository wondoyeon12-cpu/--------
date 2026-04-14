import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'slack_data.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT user_id, text, timestamp FROM messages")
rows = c.fetchall()
conn.close()

with open('db_dump.txt', 'w', encoding='utf-8') as f:
    for r in rows:
        f.write(f"[{r[2]}] {r[0]}: {r[1]}\n")
