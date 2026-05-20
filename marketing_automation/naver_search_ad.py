import hashlib
import hmac
import base64
import time
import requests
import json
import sys
import io

# Windows 콘솔 유니코드 에러 방지
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

# ==============================================================
# 🔑 네이버 검색광고 API 인증 정보
# (보안을 위해 추후에는 .env 파일 같은 환경변수로 빼는 것을 권장합니다)
# ==============================================================
CUSTOMER_ID = "4390022"
API_KEY = "0100000000a3c106b426bd48caed1b332b1624930988c3bbc65223b91b447d80f0e7062a93"
SECRET_KEY = "AQAAAACjwQa0Jr1Iyu0bMysWJJMJ1xUW/54aGHkHj/TUPz4JXA=="

BASE_URL = "https://api.naver.com"

def generate_signature(timestamp, method, path, secret_key):
    """
    네이버 검색광고 API 시그니처 생성 함수 (공식 문서 기준)
    """
    message = f"{timestamp}.{method}.{path}"
    
    # HMAC-SHA256 해싱 후 Base64 인코딩
    hash_obj = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(hash_obj.digest()).decode('utf-8')
    return signature

def get_header(method, path):
    """
    API 요청에 필요한 헤더 생성
    """
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(timestamp, method, path, SECRET_KEY)
    
    headers = {
        'X-Timestamp': timestamp,
        'X-API-KEY': API_KEY,
        'X-Customer': CUSTOMER_ID,
        'X-Signature': signature,
        'Content-Type': 'application/json'
    }
    return headers

def get_keyword_search_volume(keywords):
    """
    키워드 검색량 조회 (최대 5개 쉼표로 구분하여 전달)
    """
    path = "/keywordstool"
    method = "GET"
    
    # 파라미터 설정 (리스트면 쉼표 문자열로 변경)
    keyword_str = ",".join(keywords) if isinstance(keywords, list) else keywords
    
    params = {
        "hintKeywords": keyword_str,
        "showDetail": "1"
    }
    
    headers = get_header(method, path)
    url = BASE_URL + path
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # HTTP 에러 발생 시 예외 발생
        return response.json()
    except Exception as e:
        print(f"❌ API 요청 에러: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print("응답 내용:", response.text)
        return None

def get_top_related_keywords(keyword, limit=150):
    """
    단일 키워드로 네이버 연관 키워드를 모두 가져온 뒤,
    모바일 검색수 기준으로 내림차순 정렬하여 상위 limit개 반환
    """
    result = get_keyword_search_volume([keyword])
    if not result or 'keywordList' not in result:
        return []
        
    keyword_list = result['keywordList']
    
    def parse_cnt(val):
        if isinstance(val, str):
            val = val.replace('< ', '').replace('<', '').replace(',', '').strip()
            try:
                return int(val)
            except:
                return 0
        return int(val)
        
    def parse_float(val):
        if isinstance(val, str):
            val = val.replace('< ', '').replace('<', '').replace(',', '').strip()
            try:
                return float(val)
            except:
                return 0.0
        return float(val)
        
    for item in keyword_list:
        pc_cnt = parse_cnt(item.get('monthlyPcQcCnt', 0))
        mobile_cnt = parse_cnt(item.get('monthlyMobileQcCnt', 0))
        item['totalQcCnt'] = pc_cnt + mobile_cnt
        item['pcQcCnt'] = pc_cnt
        item['mobileQcCnt'] = mobile_cnt
        item['pcClkCnt'] = parse_float(item.get('monthlyAvePcClkCnt', 0))
        item['mobileClkCnt'] = parse_float(item.get('monthlyAveMobileClkCnt', 0))
        item['pcCtr'] = parse_float(item.get('monthlyAvePcCtr', 0))
        item['mobileCtr'] = parse_float(item.get('monthlyAveMobileCtr', 0))
        item['compIdx'] = item.get('compIdx', '')
        item['plAvgDepth'] = parse_cnt(item.get('plAvgDepth', 0))
        
    # 모바일 검색수 기준 내림차순 정렬
    sorted_list = sorted(keyword_list, key=lambda x: x['mobileQcCnt'], reverse=True)
    
    return sorted_list[:limit]

if __name__ == "__main__":
    # 테스트 키워드 (최대 5개 권장)
    test_keywords = ["관절보궁", "홍삼", "영양제"]
    
    print(f"🔍 키워드 검색량 조회 중... ({', '.join(test_keywords)})")
    
    result = get_keyword_search_volume(test_keywords)
    
    if result and 'keywordList' in result:
        print("\n✅ 조회 성공! 데이터 출력 (연관 키워드 포함):\n")
        print(f"{'키워드':<15} | {'PC 검색수':<10} | {'모바일 검색수':<12} | {'PC 클릭수':<10} | {'모바일 클릭수':<12}")
        print("-" * 75)
        
        # 연관 키워드들이 수백 개 나올 수 있으므로, 일단 15개 정도만 출력해봅니다.
        for data in result['keywordList'][:15]: 
            keyword = data.get('relKeyword', '')
            
            # API 응답에서 '< 10' 과 같이 문자열이 올 수 있으므로 str 변환 유지
            pc_monthly = data.get('monthlyPcQcCnt', 0)
            mobile_monthly = data.get('monthlyMobileQcCnt', 0)
            pc_clicks = data.get('monthlyPcClkCnt', 0)
            mobile_clicks = data.get('monthlyMobileClkCnt', 0)
            
            # 한글 포매팅을 위해 포맷팅을 단순하게 구성
            print(f"{keyword}\t\t| {str(pc_monthly)}\t| {str(mobile_monthly)}\t| {str(pc_clicks)}\t| {str(mobile_clicks)}")
    else:
        print("\n❌ 데이터를 가져오지 못했습니다.")
