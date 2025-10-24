from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMOTION_EMOJI_MAP = {
    "행복": "😊",
    "슬픔": "😢",
    "분노": "😠",
    "불안": "😰",
    "중립": "😐"
}

def format_sentence(text: str) -> str:
    text = text.strip()
    if not text.endswith(("다", "요", ".", "!", "?")):
        return text + "."
    return text

async def analyze_emotion(text: str) -> dict:
    system_prompt = (
        "당신은 감정 분석 전문가입니다.\n"
        "사용자가 작성한 일기를 읽고 감정을 다음 중 하나로 판단해 주세요: 행복, 슬픔, 분노, 불안, 중립.\n"
        "단, 중립은 감정 표현이 전혀 없는 경우에만 선택해야 하며, 조금이라도 감정이 드러난다면 가장 가까운 감정을 선택해야 합니다.\n"
        "다음 형식의 JSON으로만 출력해 주세요:\n\n"
        '{\n'
        '  "label": "행복",\n'
        '  "reason": "긍정적인 단어들이 많고 기분 좋다는 표현이 반복되었기 때문입니다.",\n'
        '  "score": 8,\n'
        '  "feedback": "오늘 하루가 정말 좋으셨군요! 그런 날이 자주 오면 좋겠어요."\n'
        '}\n\n'
        "⚠️ 반드시 JSON만 출력하세요. 다른 문장은 쓰지 마세요."
    )

    user_prompt = f"일기 내용:\n{text}"

    try:
        # ✅ 최신 openai 1.x 방식
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=2000
        )

        content = response.choices[0].message.content
        print("🧠 GPT 응답 원문:\n", content)

        parsed = json.loads(content.strip())

        label = parsed.get("label", "중립")
        emoji = EMOTION_EMOJI_MAP.get(label, "😐")

        score_raw = parsed.get("score", 5)
        try:
            score = int(round(float(score_raw)))
        except (ValueError, TypeError):
            score = 5

        return {
            "analyzed_emotion": {"label": label, "emoji": emoji},
            "reason": format_sentence(parsed.get("reason", "분석 실패")),
            "score": score,
            "feedback": format_sentence(parsed.get("feedback", "감정을 정확히 인식하지 못했어요."))
        }

    except Exception as e:
        print("❌ 감정 분석 실패:", str(e))
        return {
            "analyzed_emotion": {"label": "중립", "emoji": "😐"},
            "reason": "감정 분석에 실패했습니다.",
            "score": 5,
            "feedback": "오늘 하루도 수고 많으셨어요."
        }
