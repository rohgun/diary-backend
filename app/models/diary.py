from app.db.mongo import db
from app.schemas.diary import DiaryCreate, DiaryResponse
from datetime import datetime
from typing import List, Optional
from bson import ObjectId

# ==================================================
# ✅ 안전한 컬렉션 접근 함수
# ==================================================
def get_diary_collection():
    if db is None:
        raise RuntimeError("❌ MongoDB 연결 전 상태입니다. connect_to_mongo() 실행 필요")
    return db["diaries"]


# ==================================================
# ✅ MongoDB → DiaryResponse 변환용 serialize 함수
# ==================================================
def serialize(d: dict) -> dict:
    return {
        "id": str(d["_id"]),
        "user_id": d["user_id"],
        "date": d["date"] if isinstance(d["date"], datetime) else datetime.fromisoformat(str(d["date"])),
        "text": d["text"],
        "emotion": d.get("emotion", {"label": "알수없음", "emoji": "❓"}),
        "analyzed_emotion": d.get("analyzed_emotion", {"label": "분석실패", "emoji": "❓"}),
        "reason": d.get("reason", "분석 실패"),
        "score": d.get("score", 5),
        "feedback": d.get("feedback", "감정 분석에 실패했습니다."),
        "created_at": d.get("created_at"),
    }


# ==================================================
# ✅ 일기 생성
# ==================================================
async def create_diary(
    user_id: str,
    diary: DiaryCreate,
    analyzed_emotion: dict,
    reason: str,
    score: int,
    feedback: str,
) -> DiaryResponse:
    diary_collection = get_diary_collection()

    data = diary.dict()
    data["user_id"] = user_id
    data["emotion"] = diary.emotion.dict()
    data["analyzed_emotion"] = analyzed_emotion
    data["reason"] = reason
    data["score"] = score
    data["feedback"] = feedback
    data["created_at"] = datetime.utcnow()

    result = await diary_collection.insert_one(data)
    data["_id"] = result.inserted_id
    return DiaryResponse(**serialize(data))


# ==================================================
# ✅ 사용자 전체 일기 조회
# ==================================================
async def get_user_diaries(user_id: str) -> List[DiaryResponse]:
    diary_collection = get_diary_collection()
    diaries = []
    async for doc in diary_collection.find({"user_id": user_id}).sort("date", -1):
        diaries.append(DiaryResponse(**serialize(doc)))
    return diaries


# ==================================================
# ✅ 특정 ID로 일기 조회
# ==================================================
async def get_diary_by_id(user_id: str, diary_id: str) -> Optional[DiaryResponse]:
    diary_collection = get_diary_collection()
    try:
        diary = await diary_collection.find_one({
            "_id": ObjectId(diary_id),
            "user_id": user_id
        })
        if diary:
            return DiaryResponse(**serialize(diary))
        return None
    except Exception as e:
        print(f"❌ get_diary_by_id 오류: {e}")
        return None


# ==================================================
# ✅ 특정 날짜의 일기 조회
# ==================================================
async def get_diary_by_date(user_id: str, target_date: datetime) -> Optional[DiaryResponse]:
    diary_collection = get_diary_collection()

    doc = await diary_collection.find_one({
        "user_id": user_id,
        "date": target_date,
    })

    if doc:
        return DiaryResponse(**serialize(doc))
    return None


# ==================================================
# ✅ 일기 삭제
# ==================================================
async def delete_diary_by_id(diary_id: str) -> bool:
    diary_collection = get_diary_collection()
    result = await diary_collection.delete_one({"_id": ObjectId(diary_id)})
    return result.deleted_count > 0


# ==================================================
# ✅ 일기 수정 (UPDATE)
# ==================================================
async def update_diary_by_id(user_id: str, diary_id: str, diary: DiaryCreate) -> Optional[DiaryResponse]:
    """
    DiaryCreate(datetime, emotion, text)에 맞춰 수정
    """
    diary_collection = get_diary_collection()

    update_data = {
        "date": diary.date,
        "emotion": diary.emotion.dict(),
        "text": diary.text,
    }

    result = await diary_collection.update_one(
        {"_id": ObjectId(diary_id), "user_id": user_id},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        return None

    updated = await diary_collection.find_one({"_id": ObjectId(diary_id)})
    if updated:
        return DiaryResponse(**serialize(updated))
    return None
