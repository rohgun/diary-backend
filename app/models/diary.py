# app/models/diary.py
from app.db.mongo import db
from app.schemas.diary import DiaryCreate, DiaryResponse
from datetime import date, datetime
from typing import List, Optional
from bson import ObjectId

async def get_diary_by_id(user_id: str, diary_id: str):
    """
    특정 일기를 ID 기준으로 조회 (사용자 ID 검증 포함)
    """
    diary_collection = get_diary_collection()
    try:
        diary = await diary_collection.find_one({
            "_id": ObjectId(diary_id),
            "user_id": user_id  # 보안상 본인 일기만 조회 가능
        })
        if diary:
            diary["_id"] = str(diary["_id"])
            return DiaryResponse(**serialize(diary))
        return None
    except Exception as e:
        print(f"❌ get_diary_by_id 오류: {e}")
        return None


# ==================================================
# ✅ 안전한 컬렉션 접근 함수
# ==================================================
def get_diary_collection():
    """
    MongoDB 연결 완료 후 호출해야 함.
    db가 None이면 아직 연결되지 않은 상태이므로 명확히 예외 발생.
    """
    if db is None:
        raise RuntimeError("❌ MongoDB 연결 전 상태입니다. connect_to_mongo() 실행 필요")
    return db["diaries"]


# ==================================================
# ✅ MongoDB → DiaryResponse 변환용 serialize 함수
# ==================================================
def serialize(d: dict) -> dict:
    return {
        "id": str(d["_id"]),
        "user_id": d["user_id"],  # 문자열 그대로 반환
        "date": d["date"].date() if isinstance(d["date"], datetime) else d["date"],
        "text": d["text"],
        "emotion": d.get("emotion", {"label": "알수없음", "emoji": "❓"}),
        "analyzed_emotion": d.get("analyzed_emotion", {"label": "분석실패", "emoji": "❓"}),
        "reason": d.get("reason", "분석 실패"),
        "score": d.get("score", 5),
        "feedback": d.get("feedback", "감정 분석에 실패했습니다."),
        "created_at": d.get("created_at"),
    }


# ==================================================
# ✅ 일기 생성 함수
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
    data["user_id"] = user_id  # ObjectId 변환 ❌ → 문자열 그대로 저장
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
# ✅ 특정 날짜의 일기 조회
# ==================================================
async def get_diary_by_date(user_id: str, target_date: date) -> Optional[DiaryResponse]:
    diary_collection = get_diary_collection()
    target_datetime = datetime.combine(target_date, datetime.min.time())

    doc = await diary_collection.find_one({
        "user_id": user_id,
        "date": target_datetime,
    })

    if doc:
        return DiaryResponse(**serialize(doc))
    return None


# ==================================================
# ✅ 일기 삭제 (확장용)
# ==================================================
async def delete_diary_by_id(diary_id: str) -> bool:
    """
    필요 시 사용: 특정 일기 삭제
    """
    from bson import ObjectId
    diary_collection = get_diary_collection()
    result = await diary_collection.delete_one({"_id": ObjectId(diary_id)})
    return result.deleted_count > 0
