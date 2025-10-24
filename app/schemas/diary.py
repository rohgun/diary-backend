from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class EmotionDetail(BaseModel):
    label: str
    emoji: str

class DiaryCreate(BaseModel):
    date: datetime
    emotion: EmotionDetail
    text: str = Field(..., min_length=15)

    class Config:
        schema_extra = {
            "example": {
                "date": "2025-07-28T00:00:00",
                "emotion": {
                    "label": "슬픔",
                    "emoji": "😢"
                },
                "text": "요즘 너무 무기력하고, 아무것도 하기 싫어요. 누구한테 말할 수 없고 마음이 울적합니다."
            }
        }

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
    created_at: Optional[datetime]
