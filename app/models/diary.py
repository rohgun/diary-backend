# app/models/diary.py
from app.db.mongo import db
from app.schemas.diary import DiaryCreate, DiaryResponse
from datetime import datetime, date as _date
from typing import List, Optional
from bson import ObjectId

# ==================================================
# ✅ 안전한 컬렉션 접근
# ==================================================
def get_diary_collection():
    if db is None:
        raise RuntimeError("❌ MongoDB 연결 전 상태입니다. connect_to_mongo() 실행 필요")
    return db["diaries"]


# ==================================================
# ✅ 직렬화: Mongo 문서 -> DiaryResponse dict
# ==================================================
def _to_datetime(v) -> datetime:
    """
    date/datetime/str 모두 안전하게 datetime으로 변환
    (Mongo에서 date가 date/datetime/str로 올 수 있어 보강)
    """
    if isinstance(v, datetime):
        return v
    if isinstance(v, _date):
        return datetime.combine(v, datetime.min.time())
    if isinstance(v, str):
        # ISO 문자열 가정
        # e.g. "2025-11-05T00:00:00Z" -> +00:00
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    # None 등 예외: 지금 시각 폴백 (문서 훼손 방지)
    return datetime.utcnow()


def serialize(d: dict) -> dict:
    return {
        "id": str(d["_id"]),
        "user_id": d["user_id"],
        "date": _to_datetime(d.get("date")),
        "text": d.get("text", ""),
        "emotion": d.get("emotion", {"label": "알수없음", "emoji": "❓"}),
        "analyzed_emotion": d.get("analyzed_emotion", {"label": "분석실패", "emoji": "❓"}),
        "reason": d.get("reason", "분석 실패"),
        "score": d.get("score", 5),
        "feedback": d.get("feedback", "감정 분석에 실패했습니다."),
        "risk_level": d.get("risk_level", "none"),  # ✅ 위험도 저장/반환
        "risk_resources": d.get("risk_resources"),
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
    risk_level: str = "none",  # ✅ analyze_emotion() 결과에서 전달
    risk_resources: list[str] | None = None,
) -> DiaryResponse:
    col = get_diary_collection()

    # Pydantic 모델 → dict
    data = diary.model_dump()
    data["user_id"] = user_id
    data["emotion"] = diary.emotion.model_dump()
    data["analyzed_emotion"] = analyzed_emotion
    data["reason"] = reason
    data["score"] = score
    data["feedback"] = feedback
    data["risk_level"] = risk_level
    if risk_resources:                        # ✅ 추가
        data["risk_resources"] = risk_resources
    data["created_at"] = datetime.utcnow()

    # date 필드 정규화 (항상 datetime으로)
    data["date"] = _to_datetime(data.get("date"))

    res = await col.insert_one(data)
    data["_id"] = res.inserted_id
    return DiaryResponse(**serialize(data))


# ==================================================
# ✅ 사용자 전체 일기 조회 (최신순)
# ==================================================
async def get_user_diaries(user_id: str) -> List[DiaryResponse]:
    col = get_diary_collection()
    items: List[DiaryResponse] = []
    async for doc in col.find({"user_id": user_id}).sort("date", -1):
        items.append(DiaryResponse(**serialize(doc)))
    return items


# ==================================================
# ✅ 특정 ID로 일기 조회 (본인 것만)
# ==================================================
async def get_diary_by_id(user_id: str, diary_id: str) -> Optional[DiaryResponse]:
    col = get_diary_collection()
    try:
        doc = await col.find_one({"_id": ObjectId(diary_id), "user_id": user_id})
        return DiaryResponse(**serialize(doc)) if doc else None
    except Exception as e:
        print(f"❌ get_diary_by_id 오류: {e}")
        return None


# ==================================================
# ✅ 특정 날짜의 일기 조회 (정확 일치)
# ==================================================
async def get_diary_by_date(user_id: str, target_date: datetime) -> Optional[DiaryResponse]:
    col = get_diary_collection()
    target = _to_datetime(target_date)
    doc = await col.find_one({"user_id": user_id, "date": target})
    return DiaryResponse(**serialize(doc)) if doc else None


# ==================================================
# ✅ 일기 삭제 (본인 것만)
# ==================================================
async def delete_diary_by_id(user_id: str, diary_id: str) -> bool:
    col = get_diary_collection()
    res = await col.delete_one({"_id": ObjectId(diary_id), "user_id": user_id})
    return res.deleted_count > 0


# ==================================================
# ✅ 일기 수정 (본문/감정/날짜만 갱신)
# ==================================================
async def update_diary_by_id(user_id: str, diary_id: str, diary: DiaryCreate) -> Optional[DiaryResponse]:
    """
    DiaryCreate(date, emotion, text)에 맞춰 수정
    """
    col = get_diary_collection()

    update_data = {
        "date": _to_datetime(diary.date),
        "emotion": diary.emotion.model_dump(),
        "text": diary.text,
    }

    res = await col.update_one(
        {"_id": ObjectId(diary_id), "user_id": user_id},
        {"$set": update_data}
    )

    if res.matched_count == 0:
        # 존재X 또는 본인 소유 아님
        return None

    # modified_count가 0이어도 값 동일 가능 → 다시 조회해 반환
    updated = await col.find_one({"_id": ObjectId(diary_id), "user_id": user_id})
    return DiaryResponse(**serialize(updated)) if updated else None
