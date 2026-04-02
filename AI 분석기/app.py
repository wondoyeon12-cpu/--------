from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from openai import AsyncOpenAI
import os
import json
import base64
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# You must have OPENAI_API_KEY in your .env
api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key) if api_key and api_key != "여기에_실제_키를_넣어주세요" else None

@app.post("/analyze")
async def analyze_image(files: List[UploadFile] = File(...)):
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="이미지를 1장 이상 올려주세요.")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="이미지는 최대 5장까지만 분석 가능합니다.")

    images_content = []
    
    for file in files:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="이미지 파일만 분석 가능합니다. 사진을 올리세요.")
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode("utf-8")
        images_content.append({"type": "image_url", "image_url": {"url": f"data:{file.content_type};base64,{base64_image}", "detail": "high"}})

    prompt = """너는 냉소적인 20대 인간관계 분석가야. 말투는 아주 차갑고, 유머러스하며, 싸가지 없는 팩트 폭격기 스타일이야. 절대 친절하게 말하지 마.
사용자가 올린 최대 5장의 카톡 대화 스크린샷 텍스트를 순서대로 통합하여 분석해.

먼저 전체 텍스트에서 긍정/부정 지수(Sentiment Score)와 시간 흐름에 따른 '감정선의 변화(기승전결)'를 뽑아.
분석 요소:
1. 대화의 흐름 변화: (예: 1번 스샷에선 님이 갑이었는데 3번 스샷부터 을로 전락함, 서로 점점 식어감 등)
2. 감정 극성: '사랑해', '하트' 등 긍정 vs 'ㅇㅇ', '바빠' 등 부정
3. 권력 역학: 질문 주도권, 답장 속도 차이 (갑을관계)
4. 기싸움 지수: 읽씹/안읽씹, 심리전 여부

결과 생성 조건 (매우 중요):
A. 긍정 지수가 높을 때 (사랑하는 사이/안정적):
- d_day: '10,000일 이상(D-Forever)' 혹은 '주변 친구들이 너희를 손절할 때까지' 등 무한대의 수명
- fact_bombs: "염장 지르지 말고 둘이 평생 사귀세요", "너희 너무 붙어 있어서 공기가 부족해 죽을 지경" 등 질투 섞인 병맛 멘트 3개

B. 부정 지수가 높을 때 (싸우는 사이/깨지기 직전/썸 타다 망함):
- d_day: 'D-3', '3시간 뒤', '이미 차단됨' 등 시한부 선고
- fact_bombs: "이미 대화에 영혼이 없음. 유통기한 지남", "네 혼자 매달리는 거 불쌍해 죽겠다" 등 냉혹한 팩폭 멘트 3개

추가로, 결과창에 띄울 '심층 관계 보고서(insight_report)'를 작성해.
- 상대방의 전체적인 행동 패턴을 분석해서 썸 타는 관계 혹은 연인 사이에서의 심리학적 통찰력을 세 문장으로 요약해줘. (특히 사진의 장수가 많을수록, 대화 흐름의 변화를 꼭 짚어줄 것)
- 예시: "님이 올린 카톡 캡처를 보면, 처음엔 상대가 호감 있었는데 뒤로 갈수록 님이 질척대서 식었음.", "너희의 '대화 주도권'은 명백히 상대에게 넘어간 상태임. 고백 공격하면 즉사."

결과는 반드시 아래 JSON 형식(Markdown 백틱 제외)으로 반환할 것:
{
  "temperature": [-100부터 100 사이의 숫자. 낮을수록 파탄, 높을수록 끈끈함],
  "power_struggle_index": [0부터 100 사이의 숫자. 서로 팽팽할수록 높음],
  "d_day": ["예상 손절 시점"],
  "insight_report": ["심층 심리 분석 문구 1", "심리 분석 문구 2", "최종 결론 문구 3"],
  "fact_bombs": ["상황 맞춤형 병맛/팩폭 문구 1", "상황 맞춤형 병맛/팩폭 문구 2", "근거가 포함된 문구 3"]
}"""

    if not client:
        print("API 키가 없습니다. 더미 데이터를 반환합니다.")
        import asyncio
        await asyncio.sleep(2) # Fake delay
        return {
            "temperature": -89,
            "power_struggle_index": 99,
            "d_day": "이미 호흡 멈춤",
            "fact_bombs": [
                "야, 답장 시간 보이지? 넌 그냥 보류 명단이야.",
                "너 혼자 북치고 장구치고 애쓴다 진짜ㅋㅋ",
                "이 집착, 기싸움에서 넌 이미 완패했어. 당장 차단해."
            ]
        }

    user_message_content = [{"type": "text", "text": prompt}]
    user_message_content.extend(images_content)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": user_message_content
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=600,
        )
        
        result_json = response.choices[0].message.content
        return json.loads(result_json)
        
    except Exception as e:
        print("Error API call:", e)
        # Fallback on error
        return {
            "temperature": -50,
            "power_struggle_index": 80,
            "d_day": "통신 에러로 수명 연장됨",
            "fact_bombs": [
                "에러 나서 네 호구짓 분석 불가.",
                "카드가 한도초과 났냐? API 키 확인해라.",
                "운 좋은 줄 알아라. 팩폭 피했네."
            ]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
