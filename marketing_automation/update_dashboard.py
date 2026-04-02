import codecs
import os

fp = r"c:\Users\user\OneDrive\Desktop\에이전트프로젝트\marketing_automation\marketing_dashboard.py"
with codecs.open(fp, 'r', 'utf-8') as f:
    lines = f.readlines()

p3_start = -1
p4_start = -1
p6_start = -1

for i, l in enumerate(lines):
    if "# Pipeline 3: Stitch Prompt Generator" in l:
        p3_start = i
    if "# Pipeline 4: Google ATC Deep Scanner" in l:
        p4_start = i
    if "# ===============================" in l and i+1 < len(lines) and "# ★ 6번 파이프라인" in lines[i+1]:
        p6_start = i

if p3_start != -1 and p4_start != -1 and p6_start != -1:
    new_p3 = []
    new_p3.append("# Pipeline 3: 랜딩페이지 이미지 전체화면 캡처기 (벤치마킹 타겟 URL 스크린샷 전용)\n")
    new_p3.append("st.write(\"---\")\n")
    new_p3.append("st.header(\"📸 랜딩페이지 전체화면 캡처기\")\n")
    new_p3.append("p_ref_url = st.text_input(\"🔗 벤치마킹 타겟 URL (전체화면 캡처 용도)\")\n")
    new_p3.append("capture_button = st.button(\"📸 랜딩페이지 스크린샷 캡처\", width=\"stretch\")\n")
    new_p3.append("\n")
    new_p3.append("if capture_button and p_ref_url:\n")
    new_p3.append("    import subprocess\n")
    new_p3.append("    import time\n")
    new_p3.append("    out_img = f\"stitch_reference_temp_{int(time.time())}.jpg\"\n")
    new_p3.append("    with st.spinner(\"캡처 중...\"):\n")
    new_p3.append("        subprocess.run([\"python\", \"vision_playwright_helper.py\", p_ref_url, out_img])\n")
    new_p3.append("    st.session_state.stitch_ref_image_path = out_img\n")
    new_p3.append("    st.success(f\"✅ 캡처 완료! 파일명: {out_img}\")\n")
    new_p3.append("\n")
    new_p3.append("if st.session_state.get('stitch_ref_image_path') and os.path.exists(st.session_state.stitch_ref_image_path):\n")
    new_p3.append("    st.image(st.session_state.stitch_ref_image_path, caption=\"캡처된 전체화면 이미지\", width=\"stretch\")\n")
    new_p3.append("\n")
    new_p3.append("'''\n")
    new_p3.append("# [보관용] Google Stitch 전용 기획 프롬프트 생성기 (숨김 처리)\n")
    for l in lines[p3_start:p4_start]:
        new_p3.append(l)
    new_p3.append("'''\n")
    new_p3.append("\n")

    # Replace old p3, p4, p5 with new_p3 and then the rest starts from p6
    final_lines = lines[:p3_start] + new_p3 + lines[p6_start:]
    with codecs.open(fp, 'w', 'utf-8') as f:
        f.writelines(final_lines)
    print("SUCCESS")
else:
    print("FAILED indices:", p3_start, p4_start, p6_start)
