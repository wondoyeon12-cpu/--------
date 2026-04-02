# -*- coding: utf-8 -*-
"""5번 파이프라인 패치 스크립트"""

import re

filepath = r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트\marketing_automation\marketing_dashboard.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 패턴으로 5번 파이프라인 블록 찾기
start_marker = "# ===============================\n# ★ 5번 파이프라인 (AI 랜딩페이지 영역별 자동 기획서) 영역 [PROTOTYPE]\n# ==============================="
end_marker = '        st.success("🎉 세상에 없던 하이브리드 기획서 출력이 완료되었습니다. 우측의 카피와 좌측의 구조(뼈대)를 조합하여 스티치에서 바로 작업하세요! 🚀")'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1:
    print("ERROR: start_marker not found")
    exit(1)
if end_idx == -1:
    print("ERROR: end_marker not found")
    exit(1)

end_idx = end_idx + len(end_marker)
print(f"Found block: lines {content[:start_idx].count(chr(10))+1} to {content[:end_idx].count(chr(10))+1}")

NEW_BLOCK = '''# ===============================
# ★ 5번 파이프라인 (AI 랜딩페이지 영역별 자동 기획서) 영역 [PROTOTYPE]
# ===============================
st.write("---")
st.header("📋 다중 랜딩페이지 프랑켄슈타인 큐레이션 기획기 (Auto-Planner 2.0)")
st.markdown("스티치(Stitch)의 비전 렌더링 한계를 돌파하기 위한 코다리 특제 기능입니다. **최대 5개의 타사 랜딩페이지 통이미지를 업로드하면, GPT-4o Vision이 전체 수십 개의 조각 중 가장 구매 전환이 높은 핵심 섹션(5~15개)만을 체리피킹하여 완벽한 하이브리드 기획서를 렌더링**합니다.")

# ★ [Fix 6] 페르소나 입력창 (업로더 위에 배치)
st.markdown("#### 🧑‍🤝‍🧑 타겟 페르소나 & 톤앤매너 설정")
planner_persona_input = st.text_area(
    "교체 카피의 어투와 타겟을 지정하세요 (비워두면 전환율 극대화 기본 톤으로 자동 적용)",
    placeholder="예: 이 제품의 주 타겟은 50~60대 여성입니다. 딸이 엄마에게 건강 제품을 추천하는 듯한 따뜻하고 편안한 구어체로 작성해주세요. '엄마, 이거 한번 써봐~' 같은 느낌이면 좋겠어요.",
    height=100,
    key="planner_persona"
)

st.markdown("---")
uploaded_images = st.file_uploader("📸 분석할 다중 랜딩페이지 통이미지 업로드 (최대 5장)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_images:
    if len(uploaded_images) > 5:
        st.warning("⚠️ 최대 5장까지만 안전하게 분석할 수 있습니다. 상위 5장만 처리합니다.")
        uploaded_images = uploaded_images[:5]
        
    for ui in uploaded_images:
        st.image(ui, caption=f"업로드된 원본: {ui.name}", width=200)
        
    planner_button = st.button("🚀 프랑켄슈타인 큐레이션 기획 시작", use_container_width=True)
    
    if planner_button:
        with st.status("🛠️ GPT-4o Vision 하이브리드 엔진 가동 중...", expanded=True) as p_status:
            try:
                from PIL import Image, ImageDraw
                import io
                import base64
                
                # ★ [Fix 1] 페르소나 값 확정
                active_persona = planner_persona_input.strip() if planner_persona_input.strip() else "압도적인 전환율을 위한 강렬하고 직접적인 퍼포먼스 마케팅 톤앤매너로 작성하세요."
                
                st.write(f"↳ 1단계: {len(uploaded_images)}장의 통이미지를 900px 단위로 정밀 분할 (ID 라벨 오버레이 적용)...")
                
                chunks_data = []
                global_idx = 0
                
                for img_file in uploaded_images:
                    img = Image.open(img_file)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    width, height = img.size
                    
                    chunk_height = 900
                    num_chunks = height // chunk_height + (1 if height % chunk_height else 0)
                    
                    for i in range(num_chunks):
                        top = i * chunk_height
                        bottom = min(top + chunk_height, height)
                        chunk = img.crop((0, top, width, bottom)).copy()
                        
                        # ★ [Fix 4] ID 라벨 오버레이 — AI가 이미지-ID 매핑을 시각적으로 확인
                        draw = ImageDraw.Draw(chunk)
                        label = f" ID:{global_idx} ({img_file.name}) "
                        char_w = 7
                        box_w = len(label) * char_w + 8
                        draw.rectangle([8, 8, box_w, 30], fill=(220, 30, 30))
                        draw.text((10, 10), label, fill=(255, 255, 255))
                        
                        buffered = io.BytesIO()
                        chunk.save(buffered, format="JPEG", quality=92)
                        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                        
                        chunks_data.append({
                            "id": global_idx,
                            "img": chunk,
                            "b64": img_str,
                            "source": img_file.name
                        })
                        global_idx += 1
                
                # ★ [Fix 5] 최대 15장으로 제한
                max_send = min(len(chunks_data), 15)
                if len(chunks_data) > 15:
                    st.warning(f"⚠️ 총 {len(chunks_data)}개 조각 중 API 안정성을 위해 상위 {max_send}개만 분석합니다.")
                
                st.write(f"↳ 2단계: 총 {len(chunks_data)}개 조각 풀 확보. [1-Pass] 섹션 목록 인식 중...")
                p_status.update(label="🔬 [1-Pass] 섹션 구조 스캔 중...", state="running")
                
                # ★ [Fix 2 - 1-Pass] 각 청크가 어떤 섹션인지 먼저 목록화 (환각 방지 핵심)
                pass1_content = [{"type": "text", "text": f"""
당신은 퍼포먼스 마케팅 랜딩페이지 구조 분석 전문가입니다.
각 이미지의 좌상단에 빨간 라벨로 'ID:N' 번호가 표시되어 있습니다. 반드시 이 라벨을 기준으로 ID를 파악하세요.
총 {max_send}개의 이미지(ID 0~{max_send-1})를 순서대로 분석하여, 각 이미지가 어떤 랜딩페이지 섹션인지 파악하세요.

[출력 JSON 포맷 — 반드시 아래 형식으로만 리턴]
{{
  "chunk_map": [
    {{
      "id": 0,
      "section_type": "히어로 배너 / 사회적 증거 / 특장점 나열 / 비포·애프터 / DB 수집 폼 / CTA 버튼 / 후기·리뷰 / 브랜드 스토리 / 성분 상세 / 기타 중 가장 적합한 것",
      "content_summary": "이 이미지에 실제로 보이는 내용을 2~3문장으로 사실에만 근거하여 기술 (없는 내용 절대 추가 금지)",
      "has_cta_button": true
    }}
  ]
}}
"""}]
                
                for c_data in chunks_data[:max_send]:
                    pass1_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{c_data['b64']}", "detail": "high"}
                    })
                
                client = OpenAI(api_key=OPENAI_API_KEY)
                
                pass1_response = client.chat.completions.create(
                    model="gpt-4o",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a structural layout analyst. Return valid JSON only. Analyze only what is visually present in each image. Never hallucinate content."},
                        {"role": "user", "content": pass1_content}
                    ],
                    max_tokens=3000,
                    temperature=0.3
                )
                
                pass1_result = json.loads(pass1_response.choices[0].message.content)
                chunk_map = pass1_result.get("chunk_map", [])
                
                st.write(f"↳ 3단계: [1-Pass] 완료 ({len(chunk_map)}개 섹션 인식). [2-Pass] 체리피킹 & 카피 기획 시작...")
                p_status.update(label="✍️ [2-Pass] 체리피킹 & 맞춤 카피 생성 중...", state="running")
                
                # ★ [Fix 3 - 2-Pass] 섹션별 맞춤 카피 생성
                chunk_map_str = json.dumps(chunk_map, ensure_ascii=False, indent=2)
                
                pass2_prompt = f"""
당신은 세계 최고 수준의 퍼포먼스 마케팅 랜딩페이지 기획자입니다.
아래는 각 이미지 청크(ID:N)가 어떤 내용을 담고 있는지 1차 분석한 결과입니다:

[청크별 섹션 분석 결과]
{chunk_map_str}

[핵심 임무]
위 분석 결과를 바탕으로, 가장 강력한 구매 전환율을 만들 수 있는 섹션 최소 5개 ~ 최대 15개를 체리피킹하여 하이브리드 랜딩페이지 플로우를 기획하세요.

[★ 최우선 카피 톤앤매너 — 반드시 아래 페르소나를 100% 지켜서 모든 교체 카피를 작성할 것]
{active_persona}

[카피 작성 절대 규칙]
1. suggested_copy는 해당 섹션에 실제로 존재하는 요소에만 맞게 작성할 것 (content_summary에 없는 내용 절대 추가 금지)
2. has_cta_button이 false인 섹션에는 'CTA 버튼 문구'를 절대 포함하지 말 것
3. 섹션 유형별 카피 구성:
   - 히어로 배너: 메인 헤드라인 + 서브 카피 (CTA 있으면 버튼 문구 추가)
   - 사회적 증거/후기: 구체적인 수치·리뷰 문구 위주
   - 특장점 나열: 불릿 포인트 형식 (3~5개)
   - 비포·애프터: 전/후 상황을 대비하는 스토리텔링 문구
   - DB 수집 폼/CTA: 행동 유도 문구 + 혜택 강조 + 버튼 문구
   - 성분 상세: 성분명과 효능 설명 위주
4. 모든 교체 카피는 위에 명시된 페르소나의 어투로 최소 5줄 이상 작성할 것

[출력 JSON 포맷 — 반드시 아래 형식으로만 리턴]
{{
  "selected_sections": [
    {{
      "id": 0,
      "section_type": "섹션 역할명",
      "layout_analysis": "이미지에서 실제로 보이는 레이아웃 구성 상세 묘사",
      "rationale": "이 섹션을 선택한 마케팅 전략적 이유 — 3문장 이상",
      "suggested_copy": "페르소나 톤앤매너를 반영한 맞춤형 교체 카피 전문 (섹션 유형에 맞는 요소만, 5줄 이상)"
    }}
  ]
}}
"""
                
                pass2_response = client.chat.completions.create(
                    model="gpt-4o",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a top-tier marketing planner. Return valid JSON only. Write all copy strictly following the persona tone. Never include CTA buttons for sections that do not have them."},
                        {"role": "user", "content": pass2_prompt}
                    ],
                    max_tokens=6000,
                    temperature=0.7
                )
                
                analysis_result = json.loads(pass2_response.choices[0].message.content)
                selected_sections = analysis_result.get("selected_sections", [])
                
                p_status.update(label=f"🎉 큐레이션 완료! (총 {len(selected_sections)}개 초우량 섹션 발췌)", state="complete")
                
            except Exception as e:
                p_status.update(label="❌ 기획 엔진 오류", state="error")
                st.error(f"오류: {e}")
                import traceback
                st.code(traceback.format_exc())
                st.stop()
                
        st.markdown(f"### 🎯 [프랑켄슈타인 모드] 1등의 DNA를 이식한 하이브리드 랜딩 시안 (총 {len(selected_sections)} 섹션)")
        st.info(f"🧑‍🤝‍🧑 **적용된 페르소나:** {active_persona}")
        
        for step_idx, sec in enumerate(selected_sections):
            c_id = sec.get("id", -1)
            if c_id < 0 or c_id >= len(chunks_data):
                continue
                
            chunk_info = chunks_data[c_id]
            section_type = sec.get("section_type", "섹션")
            st.markdown(f"#### 🔎 하이브리드 섹션 {step_idx + 1} — `{section_type}` (출처: `{chunk_info['source']}`)")
            col_img, col_text = st.columns([1, 2])
            
            with col_img:
                st.image(chunk_info["img"], use_container_width=True, caption=f"체리피킹된 조각 ID: {c_id}")
                st.caption(f"📐 레이아웃: {sec.get('layout_analysis', '')}")
                
            with col_text:
                st.markdown("**💡 코다리 부장의 기획 의도:**")
                st.info(sec.get("rationale", "레이아웃 뼈대가 매우 훌륭하여 선별했습니다."))
                st.markdown("**✍️ 찰떡 맞춤 카피 교체안:**")
                st.success(sec.get("suggested_copy", "이 영역의 텍스트와 이미지를 제품에 맞게 과감히 교체하세요."))
            
            st.write("---")
            
        st.success("🎉 세상에 없던 하이브리드 기획서 출력이 완료되었습니다. 우측의 카피와 좌측의 구조(뼈대)를 조합하여 스티치에서 바로 작업하세요! 🚀")'''

new_content = content[:start_idx] + NEW_BLOCK + content[end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: File patched!")
print(f"Original length: {len(content)}, New length: {len(new_content)}")
