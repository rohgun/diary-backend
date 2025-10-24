from app.db.mongo import db
from app.schemas.diary import DiaryCreate, DiaryResponse
from datetime import date, datetime
from typing import List, Optional

diary_collection = db["diaries"]

# ✅ MongoDB → DiaryResponse 변환용 serialize 함수
def serialize(d: dict) -> dict:
    return {
        "id": str(d["_id"]),
        "user_id": d["user_id"],   # 문자열 그대로 반환
        "date": d["date"].date() if isinstance(d["date"], datetime) else d["date"],
        "text": d["text"],
        "emotion": d.get("emotion", {"label": "알수없음", "emoji": "❓"}),
        "analyzed_emotion": d.get("analyzed_emotion", {"label": "분석실패", "emoji": "❓"}),
        "reason": d.get("reason", "분석 실패"),
        "score": d.get("score", 5),
        "feedback": d.get("feedback", "감정 분석에 실패했습니다."),
        "created_at": d.get("created_at")
    }

# ✅ 일기 생성 함수
async def create_diary(
    user_id: str,
    diary: DiaryCreate,
    analyzed_emotion: dict,
    reason: str,
    score: int,
    feedback: str
) -> DiaryResponse:
    data = diary.dict()
    data["user_id"] = user_id   # ObjectId 변환 ❌ → 문자열 그대로 저장
    data["emotion"] = diary.emotion.dict()  # Pydantic 모델 → dict 변환
    data["analyzed_emotion"] = analyzed_emotion
    data["reason"] = reason
    data["score"] = score
    data["feedback"] = feedback
    data["created_at"] = datetime.utcnow()

    if isinstance(data["date"], date):
        data["date"] = datetime.combine(data["date"], datetime.min.time())

    result = await diary_collection.insert_one(data)
    data["_id"] = result.inserted_id
    return DiaryResponse(**serialize(data))

# ✅ 사용자 전체 일기 조회
async def get_user_diaries(user_id: str) -> List[DiaryResponse]:
    diaries = []
    async for doc in diary_collection.find({"user_id": user_id}).sort("date", -1):  # ObjectId 변환 ❌
        diaries.append(DiaryResponse(**serialize(doc)))
    return diaries

# ✅ 특정 날짜의 일기 조회
async def get_diary_by_date(user_id: str, target_date: date) -> Optional[DiaryResponse]:
    target_datetime = datetime.combine(target_date, datetime.min.time())

    doc = await diary_collection.find_one({
        "user_id": user_id,   # ObjectId 변환 ❌
        "date": target_datetime
    })

    if doc:
        return DiaryResponse(**serialize(doc))
    return None
from app.db.mongo import db
from app.schemas.diary import DiaryCreate, DiaryResponse
from datetime import date, datetime
from typing import List, Optional

diary_collection = db["diaries"]

# ✅ MongoDB → DiaryResponse 변환용 serialize 함수
def serialize(d: dict) -> dict:
    return {
        "id": str(d["_id"]),
        "user_id": d["user_id"],   # 문자열 그대로 반환
        "date": d["date"].date() if isinstance(d["date"], datetime) else d["date"],
        "text": d["text"],
        "emotion": d.get("emotion", {"label": "알수없음", "emoji": "❓"}),
        "analyzed_emotion": d.get("analyzed_emotion", {"label": "분석실패", "emoji": "❓"}),
        "reason": d.get("reason", "분석 실패"),
        "score": d.get("score", 5),
        "feedback": d.get("feedback", "감정 분석에 실패했습니다."),
        "created_at": d.get("created_at")
    }

# ✅ 일기 생성 함수
async def create_diary(
    user_id: str,
    diary: DiaryCreate,
    analyzed_emotion: dict,
    reason: str,
    score: int,
    feedback: str
) -> DiaryResponse:
    data = diary.dict()
    data["user_id"] = user_id   # ObjectId 변환 ❌ → 문자열 그대로 저장
    data["emotion"] = diary.emotion.dict()  # Pydantic 모델 → dict 변환
    data["analyzed_emotion"] = analyzed_emotion
    data["reason"] = reason
    data["score"] = score
    data["feedback"] = feedback
    data["created_at"] = datetime.utcnow()

    if isinstance(data["date"], date):
        data["date"] = datetime.combine(data["date"], datetime.min.time())

    result = await diary_collection.insert_one(data)
    data["_id"] = result.inserted_id
    return DiaryResponse(**serialize(data))

# ✅ 사용자 전체 일기 조회
async def get_user_diaries(user_id: str) -> List[DiaryResponse]:
    diaries = []
    async for doc in diary_collection.find({"user_id": user_id}).sort("date", -1):  # ObjectId 변환 ❌
        diaries.append(DiaryResponse(**serialize(doc)))
    return diaries

# ✅ 특정 날짜의 일기 조회
async def get_diary_by_date(user_id: str, target_date: date) -> Optional[DiaryResponse]:
    target_datetime = datetime.combine(target_date, datetime.min.time())

    doc = await diary_collection.find_one({
        "user_id": user_id,   # ObjectId 변환 ❌
        "date": target_datetime
    })

    if doc:
        return DiaryResponse(**serialize(doc))
    return None
