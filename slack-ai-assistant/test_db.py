from database import get_filtered_messages
import time

now = str(time.time())
old = str(time.time() - 86400)
msgs = get_filtered_messages(old, now, "영업 기획팀 채널")
print(f"Found {len(msgs)} messages.")
if msgs:
    print("Example:", msgs[0])
