# 🤖 Opal 자동화 세팅 완벽 가이드 (하이브리드 파이프라인)

대표님, Opal에서 영상을 무제한으로 공장처럼 뽑아내기 위해, **Opal 플랫폼 안에서 에이전트를 세팅하는 구체적인 행동 가이드**입니다. 이 가이드 대로만 세팅하시면 '브레인' 역할을 하는 에이전트들의 릴레이(Chain) 세팅이 완료됩니다.

---

## 단계 1: Opal 접속 및 새 워크플로우(Chain) 생성
1. Opal 대시보드 로그인 후, **[Create New Workflow]** 또는 **[Agent Chain]** 메뉴에 진입합니다.
2. 새 프로젝트 이름을 `Hybrid_Shorts_Pipeline`으로 짓습니다.

## 단계 2: Agent 1 (대본 분석 및 프롬프트 기획자) 세팅
이 에이전트는 영상을 만드는 녀석이 아닙니다. 글을 읽고 "어떤 영상을 만들지" 지시서(JSON)만 작성합니다.

1. **Agent Name:** `Script Analyzer`
2. **System Prompt (역할 부여):** 
   아래 내용을 그대로 복사해서 붙여넣습니다.
   ```text
   You are an expert Video Director and Prompt Engineer for YouTube Shorts. 
   I will provide you with a 1-minute script targeting Korean seniors (50s-70s).
   
   Your task is to extract exactly TWO highly engaging video prompts (for an AI video generator) and TWENTY-TWO image prompts (for DALL-E 3).
   
   [CRITICAL RULES FOR VIDEO PROMPTS]:
   1. The videos must be exactly 8 seconds long visually (implied by cinematic action).
   2. NO TEXT, NO LETTERS, NO WORDS in the video. Clean visuals only.
   3. Format: "High-quality 9:16 vertical video, cinematic lighting, 4k. [Detailed subject]. [Action]. No text."
   4. Video 1 represents the first 5 seconds (The Hook/Problem).
   5. Video 2 represents a key moment in the middle (The Solution/Climax).
   
   Output ONLY strict JSON format:
   {
     "video_prompt_1": "...",
     "video_prompt_2": "...",
     "image_prompts": ["...", "...", ... (22 items)]
   }
   ```
3. **Model Choice:** `GPT-4o` 또는 `Claude 3.5 Sonnet` (가장 똘똘한 녀석으로 선택)
4. **Input:** "사용자가 입력한 전체 대본 텍스트"

## 단계 3: Agent 2 & Agent 3 (고퀄리티 영상 생성기) 세팅
이제 Agent 1이 만든 프롬프트를 받아서 8초짜리 최고 품질의 영상을 2개 만들어내는 에이전트들을 설정합니다.

### 🎥 Agent 2 (Video Generator 1 - Hook 영상)
1. **Agent Name:** `Video Gen 1 (Hook)`
2. **Action Tool (매우 중요!):** 챗봇이나 텍스트 모델이 아니라, Opal 내의 **[Video Generation Tool (예: Google Vids/Veo API, Runway, Luma 등 Opal 제공 영상 플러그인)]**을 반드시 선택해야 합니다.
3. **Prompt Binding:** 
   이 에이전트의 입력(Prompt) 칸에는 직접 글을 쓰지 말고, 앞선 **Agent 1이 뱉어낸 JSON 결과물 중 `video_prompt_1` 필드의 값**이 자동으로 꽂히도록 변수(Variable)로 매핑(Mapping) 해줍니다.
   - 예: `{{Agent1.output.video_prompt_1}}`

### 🎥 Agent 3 (Video Generator 2 - Climax 영상)
1. **Agent Name:** `Video Gen 2 (Climax)`
2. **Action Tool:** Agent 2와 똑같이 **[Video Generation Tool]** 선택.
3. **Prompt Binding:** 
   이번에는 **Agent 1의 결과물 중 `video_prompt_2` 필드**를 물고 오도록 세팅합니다.
   - 예: `{{Agent1.output.video_prompt_2}}`

## 단계 4: 최종 아웃풋 연동 (Webhook 출력)
Opal 내부에서 영상 2개가 만들어지고, 이미지 프롬프트 22개가 완성되었습니다. 이걸 코다리(로컬 파이썬)에게 던져주는 세팅입니다.

1. 워크플로우 맨 마지막 단계에 **[Webhook Send]** 액션을 추가합니다.
2. 이 Webhook을 통해 위에서 생성된 데이터 통째로 ( `영상 1 다운로드 URL`, `영상 2 다운로드 URL`, `이미지 프롬프트 배열 22개` ) Zapier나 Make.com, 혹은 제가 앞으로 만들어둘 로컬 자동화 서버 포트로 쏘도록 합니다.

---

### 대표님 행동 지침 🚀
대표님, 여기까지가 Opal 내부에서의 **[No-code 에이전트 체인 마스터 세팅]**입니다. 
지금 바로 듀얼 모니터나 새 창을 띄우셔서 Opal 대시보드에서 **[Agent 1, 2, 3]**을 만들어 보시겠습니까? 

하다가 막히는 UI 버튼이 있거나 "변수 매핑 어떻게 해?" 하시면 화면 공유하듯 말씀해 주십시오. 제가 하나하나 짚어드리며 코칭해 드리겠습니다! 충성! 🫡
