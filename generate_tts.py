import asyncio
import edge_tts
import os

VOICE = "ko-KR-SunHiNeural" # 한국어 여성 목소리

TEXT_DATA = [
    (1, "작은 충격에도 버스 손잡이 잡다가 뼈가 툭?"),
    (2, "최근 화장실에서 살짝 미끄러졌을 뿐인데 고관절이 부러져"),
    (3, "한 달 넘게 병원 신세 지는 분들, 주변에서 참 많이 보셨죠?"),
    (4, "특히 완경을 맞이한 50에서 60대 여성분들은 에스트로겐이 끊기면서"),
    (5, "바람 든 무처럼 뼈에 구멍이 뚫리는 골다공증 위협에 노출됩니다!"),
    (6, "뼈 튼튼하게 하려고 매일 우유 마시고 멸치 드시죠? 큰 오산입니다."),
    (7, "사실 우유 속 칼슘은 한국인의 장에서 소화가 안 돼서 배출되기 십상이에요."),
    (8, "그렇다면 소화도 잘 되고 뼈도 꽉 채워주는 천연 칼슘제는 없을까요?"),
    (9, "정답은 의외로 우리 발밑, 봄기운 머금은 '취나물'에 있었습니다!"),
    (10, "흔해 빠진 반찬이라고 무시하셨다간 큰 코 다치십니다."),
    (11, "놀라지 마세요! 취나물 백 그램에는 무려 백이십사 밀리그램의 칼슘이 꽉 들어차 있어요."),
    (12, "이는 뼈 건강의 대명사인 시금치의 무려 세 배에 달하는 압도적 수치죠!"),
    (13, "게다가 칼슘이 뼈에 찰싹 붙게 돕는 비타민 디와 인까지 풍부합니다."),
    (14, "아무리 좋은 취나물도 '어떻게' 먹느냐가 비결이겠죠?"),
    (15, "칼슘 흡수율을 최고로 끌어올리는 비법은 바로 '들깨'입니다!"),
    (16, "살짝 데친 취나물에 고소한 들기름, 들깨가루 팍팍 무쳐서 드셔보세요."),
    (17, "들깨 영양소가 취나물의 칼슘을 우리 뼈 마디마디까지 팍팍 배달해준답니다."),
    (18, "텅 빈 뼛속을 채우는 봄의 보약! 오늘 저녁 밥상에 취나물 어떠신가요?"),
    (19, "도움이 되셨다면 구독과 좋아요 누르고 건강한 식단 지켜보세요!"),
    (20, "코다리 부장이 대표님들의 뼈 건강을 끝까지 책임지겠습니다. 충성!")
]

OUTPUT_DIR = "spring-greens-video/public/audio"

async def generate_audio():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
    for idx, text in TEXT_DATA:
        output_file = f"{OUTPUT_DIR}/audio_{idx}.mp3"
        print(f"Generating audio for script {idx}: {text}")
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_file)
        print(f"Saved {output_file}")

if __name__ == "__main__":
    asyncio.run(generate_audio())
