from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# ==================================================
# ✅ 감정 구조 정의
# ==================================================
class EmotionDetail(BaseModel):
    label: str
    emoji: str


# ==================================================
# ✅ 일기 작성 요청 스키마
# ==================================================
class DiaryCreate(BaseModel):
    date: datetime
    emotion: EmotionDetail
    text: str = Field(..., min_length=15)

    class Config:
        json_schema_extra = {   # ✅ pydantic v2 스타일
            "example": {
                "date": "2025-07-28T00:00:00",
                "emotion": {
                    "label": "슬픔",
                    "emoji": "😢"
                },
                "text": "요즘 너무 무기력하고, 아무것도 하기 싫어요. 누구한테 말할 수 없고 마음이 울적합니다."
            }
        }


# ==================================================
# ✅ 일기 응답 스키마
# ==================================================
class DiaryResponse(BaseModel):
    id: str
    user_id: str
    date: datetime
    text: str
    emotion: EmotionDetail
    analyzed_emotion: EmotionDetail
    reason: str
    score: int
    feedback: str
    risk_level: str = "none"              # ✅ 추가 (감정 위험 수준)
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "64b7a9f6c0eabc1234567890",
                "user_id": "abcd1234efgh5678",
                "date": "2025-07-28T00:00:00",
                "text": "요즘 너무 무기력하고 아무것도 하기 싫어요.",
                "emotion": {"label": "슬픔", "emoji": "😢"},
                "analyzed_emotion": {"label": "불안", "emoji": "😰"},
                "reason": "걱정과 불안의 표현이 강하게 나타났습니다.",
                "score": 3,
                "feedback": "오늘은 스스로에게 휴식을 허락해 주세요.",
                "risk_level": "moderate",
                "created_at": "2025-07-28T12:00:00"
            }
        }
