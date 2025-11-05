# app/models/safety.py
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from app.db.mongo import db

# ==================================================
# ✅ 리스크 통계 조회용 모델 함수
# ==================================================
async def get_recent_risk_summary(user_id: str, days: int = 30) -> Dict[str, int]:
    """
    최근 N일간 위험도 분포 (none, mild, moderate, high)
    """
    col = db["diaries"]
    start_date = datetime.utcnow() - timedelta(days=days)

    pipeline = [
        {"$match": {
            "user_id": user_id,
            "created_at": {"$gte": start_date}
        }},
        {"$set": {
            "risk": {"$ifNull": ["$risk_level", "none"]}
        }},
        {"$group": {
            "_id": "$risk",
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "risk_level": "$_id",
            "count": 1
        }}
    ]

    result = await col.aggregate(pipeline).to_list(None)
    # dict 형태로 변환 (프론트에서 바로 차트로 쓸 수 있게)
    summary = {"none": 0, "mild": 0, "moderate": 0, "high": 0}
    for r in result:
        summary[r["risk_level"]] = r["count"]
    return summary


# ==================================================
# ✅ 위험 감정 로그 리스트
# ==================================================
async def get_high_risk_entries(user_id: str, limit: int = 5) -> List[Dict]:
    """
    위험도가 'high' 또는 'moderate'인 최근 일기 n개 조회
    """
    col = db["diaries"]
    cursor = col.find(
        {"user_id": user_id, "risk_level": {"$in": ["high", "moderate"]}},
        {"_id": 0, "text": 1, "risk_level": 1, "created_at": 1}
    ).sort("created_at", -1).limit(limit)

    return await cursor.to_list(None)
