import asyncio
import json
import logging
import pandas as pd
import re
from typing import List, Dict, Any
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Page, Route, Request
from playwright_stealth import stealth

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GoogleATCScanner:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.collected_urls: List[Dict[str, Any]] = []

    async def _abort_unnecessary_resources(self, route: Route, request: Request):
        """[속도 최적화] 불필요한 이미지, 폰트, CSS(stylesheet) 로딩 차단(Abort)"""
        if request.resource_type in ["image", "font", "media", "stylesheet"]:
            await route.abort()
        else:
            await route.continue_()

    async def _handle_response(self, response):
        """
        [네트워크 가로채기]
        화면의 DOM 요소(a 태그)를 기다리지 않고, 브라우저의 네트워크 응답을 감시합니다.
        google.com/ads/rpc 또는 광고 데이터가 포함된 JSON 응답에서 직접 랜딩 URL을 추출합니다.
        """
        url = response.url
        # 구글 ATC의 백엔드 통신(RPC 요청 등) 필터링
        if "rpc" in url or "batchexecute" in url or "adstransparency" in url:
            try:
                # 응답 타입이 JSON 또는 텍스트인 경우 내부를 파싱
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type or "text/plain" in content_type:
                    text = await response.text()
                    with open("atc_debug_rpc_full.txt", "a", encoding="utf-8") as f:
                        f.write(text + "\n\n")
                    # 백슬래시 이스케이프 해제 (예: https:\/\/ -> https://)
                    text = text.replace('\\/', '/')
                    self._parse_and_store_urls_from_text(text)
            except Exception as e:
                # 스트림이 끊기거나 파싱할 수 없는 바이너리인 경우 안전하게 패스
                pass 

    def _parse_and_store_urls_from_text(self, text: str):
        """
        [동영상 광고 대응 포함]
        덤프된 응답 텍스트 블록 안에서 목적지로 의심되는 링크(Final URL)들을 정규식으로 추출합니다.
        실제 영상을 재생하지 않고도 내부 메타데이터(JSON 텍스트)에서 URL을 파싱합니다.
        """
        # http(s)로 시작하는 링크 뭉치를 정규식으로 긁어옵니다. (단순 버전)
        # 구글 광고 RPC 응답에 숨어있는 긴 파라미터 링크도 캡처
        urls = re.findall(r'(https?://[^\s",\'<>]+)', text)
        
        for u in urls:
            u_clean = u.replace('\\u003d', '=').replace('\\u0026', '&').strip('\\')
            parsed = urlparse(u_clean)
            
            netloc = parsed.netloc.lower()
            # 필터링 조건 최소화 (구글 광고/리다이렉트 URL들이 "google"을 포함하는 경우가 많음)
            if "w3.org" not in netloc and "gstatic.com" not in netloc and "googleapis" not in netloc:
                if not any(item['랜딩 URL'] == u_clean for item in self.collected_urls):
                    self.collected_urls.append({
                        "랜딩 URL": u_clean, 
                        "탐지 방식": "네트워크 응답(JSON/RPC) 가로채기"
                    })


    async def scan_keyword(self, keyword: str, limit: int = 20) -> pd.DataFrame:
        """
        주어진 키워드로 구글 투명성 센터를 스캔하여 수집된 데이터를 Pandas DataFrame으로 리턴합니다.
        """
        self.collected_urls = []
        
        async with async_playwright() as p:
            # [스텔스 강화 1]: navigator.webdriver를 false로 조작하기 위해 플래그 차단
            browser = await p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            # [스텔스 강화 2]: 최신 크롬 버전 User-Agent 설정
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            # [스텔스 강화 3]: playwright-stealth 적용 (navigator.webdriver 등 다양한 봇 탐지 속성 무효화)
            from playwright_stealth import Stealth
            await Stealth().apply_stealth_async(page)
            
            # [속도 최적화]: 불필요한 리소스(이미지/CSS 등) 요청 차단 라우팅 등록
            await page.route("**/*", self._abort_unnecessary_resources)
            
            # [네트워크 가로채기]: 응답(response) 이벤트 리스너 등록
            page.on("response", self._handle_response)
            
            try:
                # [봇 캡차 방어]: 
                # 검색 결과 페이지로 바로 가지 말고, 구글 메인 페이지에 먼저 접속해서 쿠키를 생성한 뒤 이동
                logger.info("1. 구글 메인 페이지(google.com) 접근하여 정상 사용자 쿠키 생성 중...")
                await page.goto("https://www.google.com", timeout=15000)
                await page.wait_for_timeout(2000) # 사람처럼 2초간 자연스럽게 대기
                
                # 2. ATC 투명성 센터 메인 페이지로 이동 (지역 KR)
                search_url = "https://adstransparency.google.com/?region=KR"
                logger.info(f"2. ATC 센터 메인 페이지로 이동 및 키워드 입력 준비: {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=40000)
                await page.wait_for_timeout(3000)
                
                # 3. 섀도우 DOM 등을 뚫고 검색 인풋 박스 찾아 포커스 (기존 Deep Scanner의 킬러 자바스크립트 로직 적용)
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
                
                focused = await page.evaluate(js_focus)
                if focused:
                    logger.info(f"검색창 포커스 성공. 키워드 타이핑: {keyword}")
                    await page.keyboard.type(keyword, delay=200)
                    await page.wait_for_timeout(4000)
                else:
                    logger.warning("검색창 포커스 실패. Tab 키 강제 이동 폴백 실행.")
                    for _ in range(35):
                        await page.keyboard.press("Tab")
                        await page.wait_for_timeout(100)
                    await page.keyboard.type(keyword, delay=200)
                    await page.wait_for_timeout(4000)

                # 4. 자동완성 팝업(드롭다운)에서 광고주(Advertiser) 항목만 정확하게 찾아 클릭
                logger.info("팝업 드롭다운 광고주 프로필 클릭 유도 중...")
                items = await page.locator("material-list-item, .item, [role='option']").all()
                clicked = False
                for item in items:
                    try:
                        text = await item.inner_text()
                        if "\n" in text and ("광고" in text or "인증" in text):
                            await item.click()
                            clicked = True
                            logger.info("정확한 광고주 프로필 클릭 성공!")
                            break
                    except Exception:
                        continue
                
                if not clicked:
                    logger.info("프로필을 찾지 못해 강제 Enter 입력.")
                    await page.keyboard.press("Enter")
                    
                # 5. 네트워크 통신 발생 대기 (그리드 로딩 및 RPC 덤프)
                logger.info("5. 광고 그리드 로딩 및 백그라운드 네트워크 응답 대기 (10초)...")
                await page.wait_for_timeout(10000)
                
                # 스크롤을 끝까지 내려서 추가 페이징(RPC 통신) 유도
                for _ in range(10):
                    await page.mouse.wheel(0, 3000)
                    await page.wait_for_timeout(1000)
                
            except Exception as e:
                logger.error(f"스크린 구동 중 오류 발생: {e}")
                await page.screenshot(path="atc_debug_error.png")
            finally:
                await page.screenshot(path="atc_debug_final.png")
                html_content = await page.content()
                with open("atc_debug_final.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("4. 브라우저 종료 및 자원 반환")
                await browser.close()
                
        # [Streamlit 연동]: 수집된 데이터를 Pandas DataFrame으로 리턴
        logger.info(f"[DEBUG] scan_keyword 종료 직전: collected_urls 개수 = {len(self.collected_urls)}")
        with open("atc_final_urls.txt", "w", encoding="utf-8") as f:
            f.write(f"FINAL LENGTH: {len(self.collected_urls)}\n")
        df = pd.DataFrame(self.collected_urls)
        logger.info(f"총 {len(df)} 개의 랜딩 URL 수집 완료.")
        return df

if __name__ == "__main__":
    import sys
    import json
    
    # 윈도우 환경에서 콘솔 출력 시 cp949 인코딩 에러 방지 및 utf-8 통일
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    async def main():
        keyword = sys.argv[1] if len(sys.argv) > 1 else "쿠팡"
        scanner = GoogleATCScanner(headless=True)
        # 중요 로그는 stderr로, JSON 결과는 stdout으로
        logger.setLevel(logging.INFO)
        # 로그 핸들러를 모두 stderr로 리다이렉트
        for handler in logging.root.handlers:
            handler.stream = sys.stderr
            
        df = await scanner.scan_keyword(keyword=keyword)
        
        result = {
            "status": "success",
            "keyword": keyword,
            "data": df.to_dict(orient="records")
        }
        print(f"\n##JSON_START##\n{json.dumps(result, ensure_ascii=False)}\n##JSON_END##\n")

    asyncio.run(main())
