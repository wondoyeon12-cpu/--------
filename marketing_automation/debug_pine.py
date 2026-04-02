import requests

urls = [
    "https://thepine.co.kr/smart/KCMIFf250812/NP_GDN_05_og_2_2?utm_campaign=pine&utm_source=gdn&utm_medium=cpc&utm_content=sns&utm_term=NP_GDN_05_og_2_2",
    "https://thepine.co.kr/smart/YjEHNp250626/NP_GDN_05_og_2?utm_campaign=pine&utm_source=gdn&utm_medium=cpc&utm_content=sns&utm_term=NP_GDN_05_og_2"
]

def test_headers():
    print("Testing different headers to bypass tracking link expiration...")
    
    # 1. Desktop Chrome
    headers1 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 2. iPhone Safari
    headers2 = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://www.google.com/"
    }
    
    # 3. Android Chrome from Google Ads clicking the link
    headers3 = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Referer": "https://googleads.g.doubleclick.net/"
    }

    tests = [("Desktop", headers1), ("iOS Safari", headers2), ("Android Chrome w/ Ads Referer", headers3)]
    
    for name, headers in tests:
        print(f"\n--- {name} ---")
        try:
            res = requests.get(urls[0], headers=headers, allow_redirects=True, timeout=5)
            res.encoding = 'utf-8'
            print(f"Final URL: {res.url}")
            print(f"Body: {res.text[:100]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_headers()
