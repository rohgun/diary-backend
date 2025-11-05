from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# ==================================================
# ✅ 감정 구조 정의
# ==================================================
class EmotionDetail(BaseModel):
    """
    감정 정보 (사용자 선택 / AI 분석 결과)
    """
    label: str
    emoji: str


# ==================================================
# ✅ 일기 작성 요청 스키마
# ==================================================
class DiaryCreate(BaseModel):
    """
    사용자가 새 일기를 작성할 때 요청 본문 구조
    """
    date: datetime
    emotion: EmotionDetail
    text: str = Field(..., min_length=15, description="일기 본문 (15자 이상 필수)")

    class Config:
        json_schema_extra = {
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
    """
    DB에 저장된 일기를 클라이언트로 반환할 때의 구조
    """
    id: str
    user_id: str
    date: datetime
    text: str
    emotion: EmotionDetail                   # 사용자가 직접 선택한 감정
    analyzed_emotion: EmotionDetail           # AI가 분석한 감정
    reason: str                               # 분석 근거
    score: int                                # 감정 강도 (1~10)
    feedback: str                             # AI 피드백
    risk_level: str = "none"
    risk_resources: Optional[List[dict]] = None  # ✅ 수정됨 (리소스 객체 리스트)
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
                "risk_resources": [
                    {"label": "자살예방상담 1393 (24시간)", "tel": "1393"},
                    {"label": "정신건강위기 1588-9191", "tel": "1588-9191"},
                    {"label": "국가트라우마센터", "url": "https://www.nct.go.kr"},
                ],
                "created_at": "2025-07-28T12:00:00"
            }
        }
