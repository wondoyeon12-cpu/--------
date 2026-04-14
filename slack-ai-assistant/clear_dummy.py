import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'slack_data.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("DELETE FROM messages WHERE user_id LIKE '%<@U_DUMMY_%'")
conn.commit()
print('Deleted dummy rows:', c.rowcount)
conn.close()
