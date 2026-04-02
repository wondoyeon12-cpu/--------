import requests
from urllib.parse import urlparse, urljoin
import concurrent.futures
from bs4 import BeautifulSoup
import re

# 마케터들이 자주 사용하는 대표적인 파생 단어 리스트
COMMON_PATHS = [
    "v1", "v2", "v3", "v4", "v5", 
    "event", "event1", "event2", "event3", 
    "promo", "promo1", "promo2", 
    "landing", "landing1", "landing2", "landing3",
    "test", "test1", "test2", "new", "new1", "best", "index", "main"
]
# fa1, fa2, fb1.. 숫자/영문 조합
COMMON_PATHS.extend([f"fa{i}" for i in range(1, 21)])
COMMON_PATHS.extend([f"type{i}" for i in range(1, 21)])
COMMON_PATHS.extend([f"ad{i}" for i in range(1, 21)])
COMMON_PATHS.extend([str(i) for i in range(1, 51)])

def extract_base_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def check_url(url, headers):
    try:
        # allow_redirects=False 를 유지하되, 301/302 트래킹 리다이렉트도 유효 주소로 인정
        resp = requests.get(url, headers=headers, timeout=(3.0, 5.0), allow_redirects=False)
        if resp.status_code in [200, 301, 302]:
            if resp.status_code in [301, 302]:
                loc = resp.headers.get("Location", "")
                base = extract_base_url(url)
                # 메인 페이지로 튕기는 방어벽 리다이렉트는 무시
                if loc == base or loc == base + "/" or loc == "/":
                    return None
            return url
    except Exception:
        pass
    return None

def deep_scan_sub_urls(target_url):
    """
    3중 복합 스캐너 (Sitemap, Robots.txt, multithreaded-Fuzzing)
    """
    base_url = extract_base_url(target_url)
    discovered_urls = set()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. Robots.txt 뒤지기
    try:
        robots_url = urljoin(base_url, "/robots.txt")
        resp = requests.get(robots_url, headers=headers, timeout=3)
        if resp.status_code == 200:
            paths = re.findall(r"(?:Allow|Disallow):\s*(/.*?)(?:\s|$)", resp.text)
            for path in paths:
                # 뻔한 시스템 폴더 제외
                if "wp-admin" in path or "CGI" in path:
                    continue
                full_url = urljoin(base_url, path.strip())
                if check_url(full_url, headers):
                    discovered_urls.add(full_url)
    except:
        pass

    # 2. Sitemap.xml 뒤지기
    try:
        sitemap_url = urljoin(base_url, "/sitemap.xml")
        resp = requests.get(sitemap_url, headers=headers, timeout=5)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "xml") # LXML 파서 또는 기본 XML
            for loc in soup.find_all("loc"):
                s_url = loc.text.strip()
                if s_url != base_url and s_url.startswith(base_url):
                    if check_url(s_url, headers):
                        discovered_urls.add(s_url)
    except:
        pass

    # 3. Fuzzing (마케팅 단어 무차별 난사)
    # 베이스 도메인 바로 뒤에 붙이는 패턴
    fuzzing_urls = [urljoin(base_url, f"/{p}") for p in COMMON_PATHS]
    fuzzing_urls += [urljoin(base_url, f"/{p}/") for p in COMMON_PATHS]
    fuzzing_urls += [urljoin(base_url, f"/{p}.html") for p in COMMON_PATHS]
    fuzzing_urls += [urljoin(base_url, f"/{p}.php") for p in COMMON_PATHS]
    
    # 입력한 타겟 URL 기반 패턴 (예: repi_v1 일 때 -> repi_v2 로 치환되길 노림)
    # 간단히 타겟 URL 뒤바닥에 _1 이나 /fa1 덧붙여보는 형태
    clean_target = target_url.rstrip('/')
    fuzzing_urls += [f"{clean_target}_{p}" for p in COMMON_PATHS]
    fuzzing_urls += [f"{clean_target}/{p}" for p in COMMON_PATHS]
    
    # 🎯 [핵심 추가] 스마트 변이(Mutation) 알고리즘
    # 타겟 URL 자체가 숫자로 끝난다면 (예: sw_fb1), 그걸 감지해서 숫자를 1~100까지 돌려봅니다!
    match = re.search(r"([^/]+?)(\d+)/?$", target_url)
    if match:
        prefix = match.group(1) # e.g. "sw_fb"
        base_path = target_url[:match.start()] # e.g. "https://healthlife.kr/"
        for i in range(1, 101):
            fuzzing_urls.append(f"{base_path}{prefix}{i}")
            fuzzing_urls.append(f"{base_path}{prefix}{i}/")
            fuzzing_urls.append(f"{base_path}{prefix}{i}.html")
            fuzzing_urls.append(f"{base_path}{prefix}{i}.php")
    
    unique_fuzzing = list(set(fuzzing_urls))
    
    # 초고속 병렬 스캔 (IP 블락 방지를 위해 워커 수 10으로 제한 & 명시적 비동기 종료 적용)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    future_to_url = {executor.submit(check_url, u, headers): u for u in unique_fuzzing}
    try:
        for future in concurrent.futures.as_completed(future_to_url, timeout=40):
            try:
                res = future.result()
                if res and res != base_url and res != target_url:
                    discovered_urls.add(res)
            except Exception:
                pass
    except concurrent.futures.TimeoutError:
        pass # 타임아웃 발생 시 현재까지 수집된 것만 반환
    finally:
        # 종료 시 대기(wait)하지 않고 백그라운드 스레드로 던짐 (Hanging 방지)
        executor.shutdown(wait=False, cancel_futures=True)

    return list(discovered_urls)
