import re

with open('atc_debug_rpc_full.txt', encoding='utf-8') as f:
    text = f.read()

urls = re.findall(r'(https?://[^\s",\'<>\\]+)', text)
ext_urls = set()
for u in urls:
    ul = u.lower()
    if not any(d in ul for d in ['google', 'gstatic', 'youtube', 'tpc.googlesyndication']):
        ext_urls.add(u)

print("External URLs Found:")
for u in sorted(ext_urls):
    print(u)
if not ext_urls:
    print("NONE")
