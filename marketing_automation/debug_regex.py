import re

with open('atc_debug_rpc.txt', encoding='utf-8') as f:
    text = f.read()

idx = text.find('displayads')
snippet = text[idx-50:idx+200]
print("Snippet:", snippet)

# text에서 어떻게 잡혔는지 확인
urls = re.findall(r'(https?://[^\s",\'<>]+)', snippet)
print("Extracted:", urls)

# \u003d 를 분해 후
snippet_decoded = snippet.encode().decode('unicode_escape')
print("Decoded snippet:", snippet_decoded)
urls_decoded = re.findall(r'(https?://[^\s",\'<>]+)', snippet_decoded)
print("Extracted decoded:", urls_decoded)
