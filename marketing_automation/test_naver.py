import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}
url = 'https://ad.search.naver.com/search.naver?where=ad&query=관절보궁'

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

print("Status Code:", response.status_code)

# 파워링크 리스트들은 대부분 'li' 태그 안에 존재합니다.
for a_tag in soup.select('a.lnk_tit'):
    print("Title:", a_tag.text)
    print("Link:", a_tag.get('href'))

for a_url in soup.select('.url'):
    print("URL Disp:", a_url.text)
