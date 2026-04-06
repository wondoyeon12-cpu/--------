import asyncio
import json
import logging
import pandas as pd
import re
import sys
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
                # 응답 타입인 JSON 또는 텍스트인 경우 내부를 파싱
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type or "text/plain" in content_type:
                    text = await response.text()
                    # 백슬래시 이스케이프 해제 (예: https:\/\/ -> https://)
                    text = text.replace('\\/', '/')
                    self._parse_and_store_urls_from_text(text)
            except Exception:
                # 스트림이 끊기거나 파싱할 수 없는 바이너리인 경우 안전하게 패스
                pass 

    def _parse_and_store_urls_from_text(self, text: str):
        """
        [동영상 광고 대응 포함]
        덤프된 응답 텍스트 블록 안에서 목적지로 의심되는 링크(Final URL)들을 정규식으로 추출합니다.
        실제 영상을 재생하지 않고도 내부 메타데이터(JSON 텍스트)에서 URL을 파싱합니다.
        """
        # http(s)로 시작하는 링크 뭉치를 정규식으로 긁어옵니다. (단순 버전)
        urls = re.findall(r'(https?://[^\s",\'<>]+)', text)
        
        for u in urls:
            u_clean = u.replace('\\u003d', '=').replace('\\u0026', '&').strip('\\')
            parsed = urlparse(u_clean)
            
            netloc = parsed.netloc.lower()
            # 필터링 조건 최소화
            if netloc and "w3.org" not in netloc and "gstatic.com" not in netloc and "googleapis" not in netloc:
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
            browser = None
            try:
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
                
                # [스텔스 강화 3]: playwright-stealth 적용
                from playwright_stealth import Stealth
                await Stealth().apply_stealth_async(page)
                
                # [속도 최적화]: 불필요한 리소스 요청 차단 라우팅 등록
                await page.route("**/*", self._abort_unnecessary_resources)
                
                # [네트워크 가로채기]: 응답(response) 이벤트 리스너 등록
                page.on("response", self._handle_response)
                
                try:
                    # 1. 구글 메인 페이지 접근
                    logger.info("1. 구글 메인 페이지 접근 중...")
                    await page.goto("https://www.google.com", timeout=15000)
                    await page.wait_for_timeout(2000)
                    
                    # 2. ATC 투명성 센터 메인 페이지로 이동
                    search_url = "https://adstransparency.google.com/?region=KR"
                    logger.info(f"2. ATC 센터 이동: {search_url}")
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=40000)
                    await page.wait_for_timeout(3000)
                    
                    # 3. 검색창 포커스 및 키워드 입력
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
                        await page.keyboard.type(keyword, delay=200)
                        await page.wait_for_timeout(4000)
                    else:
                        for _ in range(35):
                            await page.keyboard.press("Tab")
                        await page.keyboard.type(keyword, delay=200)
                        await page.wait_for_timeout(4000)

                    # 4. 광고주 프로필 클릭
                    items = await page.locator("material-list-item, .item, [role='option']").all()
                    clicked = False
                    for item in items:
                        try:
                            text = await item.inner_text()
                            if "\n" in text and ("광고" in text or "인증" in text):
                                await item.click()
                                clicked = True
                                break
                        except Exception:
                            continue
                    
                    if not clicked:
                        await page.keyboard.press("Enter")
                        
                    # 5. 네트워크 통신 발생 대기
                    await page.wait_for_timeout(10000)
                    for _ in range(10):
                        await page.mouse.wheel(0, 3000)
                        await page.wait_for_timeout(1000)
                    
                except Exception as e:
                    logger.error(f"스크린 구동 중 오류: {e}")
            except Exception as e:
                logger.error(f"Browser launch failed: {e}")
            finally:
                if browser:
                    logger.info("4. 브라우저 종료")
                    await browser.close()
                
        df = pd.DataFrame(self.collected_urls)
        logger.info(f"총 {len(df)} 개의 랜딩 URL 수집 완료.")
        return df

if __name__ == "__main__":
    async def main():
        keyword = sys.argv[1] if len(sys.argv) > 1 else "다이어트"
        scanner = GoogleATCScanner(headless=True)
        df = await scanner.scan_keyword(keyword=keyword)
        print(df.to_json(orient="records", force_ascii=False))

    asyncio.run(main())
