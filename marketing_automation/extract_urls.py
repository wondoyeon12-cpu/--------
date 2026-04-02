import re
import json

with open('atc_debug_rpc.txt', encoding='utf-8') as f:
    text = f.read()

text = text.replace('\\/', '/')
urls = set(re.findall(r'(https?://[^\s",\'<>\\]+)', text))

with open('atc_urls_dump.txt', 'w', encoding='utf-8') as f:
    for u in sorted(urls):
        f.write(u + '\n')
