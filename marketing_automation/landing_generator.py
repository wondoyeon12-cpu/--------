import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader
import urllib.request
import sys

# Windows CLI 인코딩 에러 방지를 위한 표준 출력 utf-8 강제 적용 (또는 이모지 사용 자제)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# 환경변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 경로 세팅
BASE_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = BASE_DIR / "FOS_Landing" / "templates"
OUTPUT_DIR = BASE_DIR / "marketing_automation" / "outputs" / "landing_pages"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_landing_copy(product_name, target_audience, keywords):
    """GPT-4o-mini를 이용한 카피라이팅 및 랜딩페이지 구조화"""
    print("[1/4] AI 텍스트 카피 작성 중...")
    prompt = f"""
    당신은 업계 최고 수준의 퍼포먼스 마케터이자 랜딩페이지 기획자입니다.
    다음 정보를 바탕으로 수익을 극대화할 수 있는 랜딩페이지 카피라이팅을 5개 섹션으로 분할하여 JSON 형식으로 작성해주세요.
    
    [제품명]: {product_name}
    [타겟 고객]: {target_audience}
    [강조 키워드]: {keywords}
    
    응답은 순수 JSON 형식이어야 하며, 아래 키워드를 정확히 포함하세요 (마크다운 포맷 불가):
    {{
        "landing_title": "브라우저 탭 타이틀",
        "hero_head": "헤드라인 (Hook - 타겟의 시선을 확 잡아끄는 문구)",
        "hero_sub": "서브 헤드라인 (가치 제안)",
        "hero_cta": "메인 버튼 텍스트",
        "prob_head": "문제 제기 헤드라인 (강한 공감대 형성)",
        "prob_desc": "결핍을 짚어주는 설명 (페인포인트 자극)",
        "sol_head": "해결책/솔루션 헤드라인 (상품이 어떻게 해결해주는가)",
        "sol_desc": "서비스/제품이 어떻게 문제를 해결하는지 명쾌하게 설명",
        "feat_head": "강력한 베네핏/소셜프루프 헤드라인",
        "feat_desc": "구체적인 이점 및 기능 설명",
        "cta_head": "마지막 행동 촉구 헤드라인",
        "cta_desc": "망설임을 없애주는 마지막 설득 멘트",
        "cta_button": "강력하고 행동 지향적인 버튼 텍스트"
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7
    )
    
    return json.loads(response.choices[0].message.content)

def generate_section_images(product_name, copy_data):
    """DALL-E 3를 이용한 섹션별 맞춤 이미지 생성"""
    print("[2/4] AI 이미지 렌더링 중 (소요 시간 약 30~60초)...")
    
    sections = [
        ("hero_img", f"A premium, modern advertising hero image for {product_name}. Concept: {copy_data['hero_head']}. High quality, cinematic lighting, corporate premium feel."),
        ("prob_img", f"A visually striking image representing the problem/pain point: {copy_data['prob_head']}. Emotional, relatable, slightly moody. Modern style."),
        ("sol_img", f"A bright, positive, satisfying image showing the solution concept: {copy_data['sol_head']}. Modern, clean, sleek tech vibe."),
        ("feat_img", f"A conceptual 3D illustration representing key benefits: {copy_data['feat_head']}. Abstract, high-tech visualization, premium quality.")
    ]
    
    img_paths = {}
    
    for key, img_prompt in sections:
        try:
            print(f"  -> [{key}] 이미지 API 호출 중...")
            response = client.images.generate(
                model="dall-e-3",
                prompt=img_prompt + " IMPORTANT: ABSOLUTELY NO TEXT in the image. Beautiful lighting, 4k, photorealistic.",
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            
            # 이미지 다운로드 및 로컬 저장
            image_filename = f"{int(time.time())}_{key}.png"
            image_filepath = OUTPUT_DIR / image_filename
            urllib.request.urlretrieve(image_url, image_filepath)
            
            # HTML에서 이미지를 불러올 수 있도록 로컬 절대경로 삽입
            img_paths[key] = f"file:///{str(image_filepath.resolve()).replace(os.sep, '/')}"
            time.sleep(1) # API Rate Limit 방지
            
        except Exception as e:
            print(f"[오류] 이미지 생성 실패 ({key}): {e}")
            img_paths[key] = f"https://via.placeholder.com/1024x768?text={key}+Error"
            
    return img_paths

def build_landing_page(product_name, target_audience, keywords):
    """완전 자동화 랜딩페이지 시안 생성 통합 파이프라인"""
    print("[코다리] 랜딩페이지 시안 제작기 파이프라인 가동!")
    print("-" * 50)
    
    # 1. 텍스트 카피라이팅 생성
    copy_data = generate_landing_copy(product_name, target_audience, keywords)
    
    # 2. 이미지 생성
    img_data = generate_section_images(product_name, copy_data)
    
    # 3. 데이터 병합
    print("[3/4] 데이터 합성 중...")
    template_data = {**copy_data, **img_data}
    
    # 4. HTML 렌더링
    print("[4/4] 프리미엄 HTML 시안 조립 중...")
    env = FileSystemLoader(str(TEMPLATE_DIR))
    jinja_env = Environment(loader=env)
    
    try:
        template = jinja_env.get_template("premium_base.html")
    except Exception as e:
        print(f"템플릿 로드 에러 (가급적 `FOS_Landing/templates/premium_base.html` 경로를 확인하세요): {e}")
        return
        
    output_html = template.render(**template_data)
    
    output_file = OUTPUT_DIR / f"prototype_{int(time.time())}.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output_html)
        
    print("-" * 50)
    print(f"성공! 완벽한 랜딩페이지 시안이 만들어졌습니다.")
    print(f"확인 경로: {output_file.resolve()}")
    return str(output_file.resolve())

if __name__ == "__main__":
    # Test Data: 1인 기업가를 위한 AI 비서 
    test_product = "코다리 AI - 1인 기업가 전용 올인원 전천후 개발/마케팅 비서"
    test_target = "디자인, 프론트/백엔드 개발을 할 줄 모르지만 번뜩이는 아이디어가 넘치고, 당장 이번주에 비즈니스를 런치하고 싶은 1인 기업 대표님"
    test_keywords = "초가성비, 야근 제로, 기술 장벽 해소, 무한 자동화, 외주 비용 0원, 프리미엄 퀄리티 보장"
    
    build_landing_page(test_product, test_target, test_keywords)
