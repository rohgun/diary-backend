from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# 보조 서비스
from app.services.resource import get_resources  # ✅ 새로 추가 (리스크별 리소스 제공)
from app.services.safety import evaluate_risk_level  # ✅ 위험 수준 정제용 (있으면 사용, 없으면 무시해도 됨)

# ==================================================
# ✅ 환경 설정
# ==================================================
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==================================================
# ✅ 감정 → 이모지 매핑
# ==================================================
EMOTION_EMOJI_MAP = {
    "행복": "😊",
    "슬픔": "😢",
    "분노": "😠",
    "불안": "😰",
    "중립": "😐"
}


# ==================================================
# ✅ 문장 마무리 보정
# ==================================================
def format_sentence(text: str) -> str:
    text = text.strip()
    if not text.endswith(("다", "요", ".", "!", "?")):
        return text + "."
    return text


# ==================================================
# ✅ 감정 분석 + 위험 감정 감지 + 리소스 추천
# ==================================================
async def analyze_emotion(text: str) -> dict:
    system_prompt = (
        "당신은 감정 분석 전문가이자 심리 상담 보조 시스템입니다.\n"
        "사용자의 일기 내용을 분석하여 다음 정보를 반드시 JSON 형식으로 제공합니다:\n\n"
        "{\n"
        '  "label": "감정 이름 (행복, 슬픔, 분노, 불안, 중립 중 하나)",\n'
        '  "reason": "이 감정을 판단한 이유",\n'
        '  "score": 1~10 사이의 감정 강도 점수 (10은 매우 강한 감정)",\n'
        '  "feedback": "사용자에게 전할 따뜻한 한 문장",\n'
        '  "risk_level": "none | mild | moderate | high 중 하나"  // ⚠️ 자살, 자해 등 위험 감정 판단 시 high\n'
        "}\n\n"
        "⚠️ 반드시 JSON 형식만 출력하세요.\n"
        "다른 문장은 출력하지 마세요.\n\n"
        "※ 'risk_level' 기준:\n"
        "- 'high': 자살, 죽고 싶다, 끝내고 싶다, 삶을 포기, 해를 입히고 싶다 등의 표현이 명확히 있을 때\n"
        "- 'moderate': 극심한 무기력, 자책, 절망, '의욕이 없다', '너무 힘들다' 등의 반복적 표현\n"
        "- 'mild': 일시적인 우울, 지침, 피로감\n"
        "- 'none': 위험 징후 없음"
    )

    user_prompt = f"일기 내용:\n{text}"

    try:
        # ✅ GPT 감정 분석
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )

        content = response.choices[0].message.content
        print("🧠 GPT 응답 원문:\n", content)

        parsed = json.loads(content.strip())

        # 기본값 안전 처리
        label = parsed.get("label", "중립")
        emoji = EMOTION_EMOJI_MAP.get(label, "😐")
        reason = format_sentence(parsed.get("reason", "분석 실패"))
        feedback = format_sentence(parsed.get("feedback", "감정을 정확히 인식하지 못했습니다."))
        risk_level = parsed.get("risk_level", "none").lower()

        # ✅ 점수 정제
        try:
            score = int(round(float(parsed.get("score", 5))))
        except (ValueError, TypeError):
            score = 5

        # ==================================================
        # ✅ 키워드 기반 백업 위험 감정 감지
        # ==================================================
        text_lower = text.lower()
        high_keywords = ["죽고 싶", "자살", "끝내고 싶", "없어지고 싶", "살기 싫", "그만 살고"]
        moderate_keywords = ["너무 힘들", "지쳤", "무기력", "포기", "괴로워", "버티기 힘들"]

        if any(kw in text_lower for kw in high_keywords):
            risk_level = "high"
        elif risk_level == "none" and any(kw in text_lower for kw in moderate_keywords):
            risk_level = "moderate"

        # ✅ safety.py 로직과 병합 (선택적)
        try:
            refined = evaluate_risk_level(text, label, score)
            if refined in ["high", "moderate", "mild"]:
                risk_level = refined
        except Exception:
            pass

        # ==================================================
        # ✅ 위험 수준별 리소스 추천 추가
        # ==================================================
        risk_resources = get_resources(risk_level)

        # ==================================================
        # ✅ 최종 응답 구조
        # ==================================================
        return {
            "analyzed_emotion": {"label": label, "emoji": emoji},
            "reason": reason,
            "score": score,
            "feedback": feedback,
            "risk_level": risk_level,
            "risk_resources": risk_resources,
        }

    except Exception as e:
        print("❌ 감정 분석 실패:", str(e))
        return {
            "analyzed_emotion": {"label": "중립", "emoji": "😐"},
            "reason": "감정 분석에 실패했습니다.",
            "score": 5,
            "feedback": "오늘 하루도 수고 많으셨어요.",
            "risk_level": "none",
            "risk_resources": get_resources("none"),
        }
