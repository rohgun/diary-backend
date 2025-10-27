from datetime import datetime, date
from bson import ObjectId
from bson.errors import InvalidId
from typing import List, Optional
from app.db.mongo import db
from app.schemas.diary import DiaryCreate, DiaryResponse
from fastapi import HTTPException

diary_collection = db["diaries"]

# ✅ MongoDB → DiaryResponse 변환용 serialize 함수
def serialize(d: dict) -> dict:
    return {
        "id": str(d["_id"]),
        "user_id": d["user_id"],   # 문자열 그대로
        "date": d["date"].date() if isinstance(d["date"], datetime) else d["date"],
        "text": d["text"],
        "emotion": d.get("emotion", {"label": "알수없음", "emoji": "❓"}),
        "analyzed_emotion": d.get("analyzed_emotion", {"label": "분석실패", "emoji": "❓"}),
        "reason": d.get("reason", "분석 실패"),
        "score": d.get("score", 5),
        "feedback": d.get("feedback", "감정 분석에 실패했습니다."),
        "created_at": d.get("created_at"),
    }

# ✅ 유효한 ObjectId인지 검사하는 함수
def is_valid_object_id(id_str: str) -> bool:
    try:
        ObjectId(id_str)
        return True
    except InvalidId:
        return False

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
    data["user_id"] = user_id   # ObjectId ❌, 문자열 그대로 ✅
    data["analyzed_emotion"] = analyzed_emotion
    data["reason"] = reason
    data["score"] = score
    data["feedback"] = feedback
    data["created_at"] = datetime.utcnow()

    # date 필드 보정
    if isinstance(data["date"], date):
        data["date"] = datetime.combine(data["date"], datetime.min.time())

    result = await diary_collection.insert_one(data)
    data["_id"] = result.inserted_id
    return DiaryResponse(**serialize(data))

# ✅ 사용자 전체 일기 조회
async def get_user_diaries(user_id: str) -> List[DiaryResponse]:
    diaries = []
    async for doc in diary_collection.find({"user_id": user_id}).sort("date", -1):
        diaries.append(DiaryResponse(**serialize(doc)))
    return diaries

# ✅ 특정 날짜의 일기 조회
async def get_diary_by_date(user_id: str, target_date: date) -> Optional[DiaryResponse]:
    target_datetime = datetime.combine(target_date, datetime.min.time())

    doc = await diary_collection.find_one({
        "user_id": user_id,
        "date": target_datetime
    })

    if doc:
        return DiaryResponse(**serialize(doc))
    return None

# ✅ id 기준 일기 조회
async def get_diary_by_id(user_id: str, diary_id: str) -> Optional[DiaryResponse]:
    # Clean the diary_id
    diary_id = diary_id.strip()

    # Validate the diary_id
    if not is_valid_object_id(diary_id):
        raise HTTPException(status_code=400, detail="Invalid diary ID provided.")

    doc = await diary_collection.find_one({
        "_id": ObjectId(diary_id),
        "user_id": user_id
    })
    if doc:
        return DiaryResponse(**serialize(doc))
    return None

# ✅ 일기 수정 함수
async def update_diary(user_id: str, diary_id: str, diary: DiaryCreate) -> Optional[DiaryResponse]:
    update_data = diary.dict()

    # emotion 필드 dict 변환 (Pydantic 모델 대비)
    if hasattr(diary, "emotion") and diary.emotion is not None:
        update_data["emotion"] = diary.emotion.dict()

    # date 보정 (datetime으로 변환)
    if isinstance(update_data.get("date"), date):
        update_data["date"] = datetime.combine(update_data["date"], datetime.min.time())

    result = await diary_collection.find_one_and_update(
        {"_id": ObjectId(diary_id), "user_id": user_id},  # 조건: 사용자 + 일기 id
        {"$set": update_data},
        return_document=True
    )

    if result:
        return DiaryResponse(**serialize(result))
    return None

# ✅ 일기 삭제 (id 기준)
async def delete_diary(user_id: str, diary_id: str) -> bool:
    result = await diary_collection.delete_one({
        "_id": ObjectId(diary_id),
        "user_id": user_id
    })
    return result.deleted_count > 0