import sys
import time
import json
import requests
from playwright.sync_api import sync_playwright

def scan_atc_for_hidden_links(keyword):
    found_targets = []
    seen_hrefs = set()
    
    with sync_playwright() as p:
        # --disable-blink-features=AutomationControlled 로 봇 탐지 우회
        browser = p.chromium.launch(headless=True, args=[
            '--disable-web-security', 
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-blink-features=AutomationControlled'
        ])
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            page.goto("https://adstransparency.google.com/?region=KR", wait_until="domcontentloaded", timeout=40000)
            time.sleep(5)
            
            js_focus = """() => {
                function findInput(root) {
                    if (!root) return null;
                    if (root.tagName === 'INPUT') return root;
                    let children = Array.from(root.children);
                    if (root.shadowRoot) children = children.concat(Array.from(root.shadowRoot.children));
                    for (let child of children) {
                        let res = findInput(child);
                        if (res) return res;
                    }
                    return null;
                }
                let inp = findInput(document.body);
                if (inp) {
                    inp.focus();
                    return true;
                }
                return false;
            }"""
            
            focused = page.evaluate(js_focus)
            if focused:
                page.keyboard.type(keyword, delay=200)
                time.sleep(5)
            else:
                # 탭을 훨씬 더 많이 눌러보도록 방어 코드 (Fallback)
                for i in range(35):
                    page.keyboard.press("Tab")
                    time.sleep(0.1)
                page.keyboard.type(keyword, delay=200)
                time.sleep(5)
            
            # 2. 자동완성 팝업(드롭다운)에서 광고주(Advertiser) 항목만 정확하게 클릭
            items = page.locator("material-list-item, .item, [role='option']").all()
            clicked = False
            for item in items:
                try:
                    text = item.inner_text()
                    # 광고주 프로필 항목은 줄바꿈(\n)을 포함합니다.
                    if "\n" in text and ("광고" in text or "인증" in text):
                        item.click()
                        clicked = True
                        break
                except Exception:
                    continue
            
            if not clicked:
                page.keyboard.press("Enter")
                
            # 3. 광고 카드 그리드 로딩 대기
            time.sleep(8)
            
            # 4. ATC는 가상 스크롤(Virtualization)을 사용하여 화면에 보이는 Iframe만 렌더링하고 위쪽은 DOM에서 지워버립니다.
            # 따라서 '스크롤을 내리면서 동시에 계속 추출'해야 600개의 광고를 모두 긁어올 수 있습니다.
            for scroll_step in range(20): # 줄였습니다 (35 -> 20)
                frames = page.frames
                for frame in frames:
                    try:
                        # image-anchor 형태 스캔
                        anchors = frame.locator("a#image-anchor").all()
                        for a in anchors:
                            href = a.get_attribute("href")
                            if href and href not in seen_hrefs:
                                seen_hrefs.add(href)
                                found_targets.append({
                                    "source_url": page.url, 
                                    "hidden_url": href, 
                                    "type": "image-anchor (Fake YouTube)"
                                })
                                
                        # 만약 id="image-anchor"가 아니더라도, a 태그 안에 i.ytimg.com 썸네일이 있는 경우 포착
                        general_anchors = frame.locator("a").all()
                        for a in general_anchors:
                            href = a.get_attribute("href")
                            if href and href not in seen_hrefs and href.startswith("http") and "youtube.com" not in href and "google.com" not in href:
                                inner_html = a.inner_html()
                                if "ytimg.com" in inner_html and ("play-triangle" in inner_html or "play" in inner_html.lower()):
                                    seen_hrefs.add(href)
                                    found_targets.append({
                                        "source_url": page.url, 
                                        "hidden_url": href, 
                                        "type": "custom-fake-youtube-anchor"
                                    })
                    except Exception:
                        continue
                        
                # 추출 후 마우스 스크롤 1페이지 분량 이동
                page.mouse.wheel(0, 2000)
                time.sleep(0.8) # 새 프레임 렌더링 대기 시간을 줄여 속도 최적화
                            
        except Exception as e:
            try: page.screenshot(path="atc_error.png")
            except: pass
            print(json.dumps({"error": f"Scraper exception: {e}", "status": "failed"}), file=sys.stderr)
        finally:
            browser.close()
            
    return found_targets

def resolve_final_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Referer": "https://adstransparency.google.com/"
    }
    try:
        res = requests.get(url, headers=headers, allow_redirects=True, timeout=5)
        res.encoding = 'utf-8'
        final_url = res.url
        if len(res.text) < 100 and ("만료" in res.text or "기간" in res.text):
            return f"[서버차단/만료됨] {url}"
        return final_url
    except Exception:
        return url

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No keyword provided"}))
        sys.exit(1)
        
    keyword = sys.argv[1]
    
    # 딥 스캔 실행 (Iframe 내부 직접 적출)
    raw_results = scan_atc_for_hidden_links(keyword)
    
    # 각 추적 링크의 최종 도착지(리다이렉트) 추론 병렬 처리 (속도 개선)
    final_results = []
    import concurrent.futures
    
    def process_item(item):
        raw_href = item["hidden_url"]
        resolved = resolve_final_url(raw_href)
        return {
            "source_url": item["source_url"],
            "raw_url": raw_href,
            "resolved_url": resolved,
            "type": item["type"]
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        final_results = list(executor.map(process_item, raw_results))
    
    # JSON으로 반환
    print(json.dumps({
        "status": "success",
        "scanned_count": len(final_results),
        "results": final_results
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
