import os
from slack_sdk import WebClient
from dotenv import load_dotenv
import sqlite3

load_dotenv()
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

print("--- USER MAP ---")
try:
    users_res = client.users_list()
    for u in users_res.get("members", []):
        uid = u.get("id")
        uname = u.get("real_name") or u.get("name")
        print(f"{uid}: {uname}")
except Exception as e:
    print(e)
    
print("\n--- CHANNEL MAP ---")
try:
    ch_res = client.conversations_list(types="public_channel,private_channel")
    for c in ch_res.get("channels", []):
        cid = c.get("id")
        cname = c.get("name")
        print(f"{cid}: {cname}")
except Exception as e:
    print(e)

print("\n--- DB MESSAGES (Last 5) ---")
conn = sqlite3.connect(os.getenv("DB_FILEPATH", "slack_data.db"))
c = conn.cursor()
c.execute("SELECT id, channel_id, user_id, timestamp, text FROM messages ORDER BY id DESC LIMIT 5")
for r in c.fetchall():
    print(r)
conn.close()
