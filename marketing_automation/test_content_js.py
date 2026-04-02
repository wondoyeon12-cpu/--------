import requests
import re

url = "https://displayads-formats.googleusercontent.com/ads/preview/content.js?client=ads-integrity-transparency&obfuscatedCustomerId=1577922613&creativeId=778855606737&uiFeatures=12"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://adstransparency.google.com/"
}
res = requests.get(url, headers=headers)
text = res.text

print("Length of content.js:", len(text))
urls = set(re.findall(r'(https?://[^\s",\'<>\\]+)', text))

print("Extracted URLs:")
for u in urls:
    if "gstatic" not in u and "googleusercontent" not in u and "googlesyndication" not in u and "google.com" not in u:
        print(u)
