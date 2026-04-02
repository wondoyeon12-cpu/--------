import subprocess
import sys
import json
import os

helper_script_atc = os.path.join(os.path.dirname(__file__), "atc_playwright_spider.py")
atc_keyword = "파인네스트"

print(f"Testing with keyword: {atc_keyword}")

try:
    result_atc = subprocess.run(
        [sys.executable, helper_script_atc, atc_keyword],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180
    )
except subprocess.TimeoutExpired:
    print("Timeout")
    sys.exit(1)

out_text = result_atc.stdout
print("STDOUT length:", len(out_text))
print("STDOUT preview:", out_text[:500])

import re
match = re.search(r"##JSON_START##(.*?)##JSON_END##", out_text, re.DOTALL)

if match:
    json_str = match.group(1).strip()
    try:
        atc_data = json.loads(json_str)
        data_list = atc_data.get("data", [])
        print(f"SUCCESS: Loaded {len(data_list)} records from JSON!")
        if data_list:
            print("First record:", data_list[0])
    except Exception as e:
        print(f"JSON Parse Error: {e}")
else:
    print("NO MATCH FOUND IN STDOUT")
    print("STDERR:", result_atc.stderr)
