# app/routes/stats.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from app.auth.jwt import get_current_user_id
from app.db.mongo import db

router = APIRouter(prefix="/stats", tags=["Stats"])

TZ = "Asia/Seoul"


# ==================================================
# ✅ 최근 5주 주간 통계 (라벨: "MM/DD ~ MM/DD")
#    - analyzed_emotion.label 기준 빈도 + 평균 score
#    - 타임존 고정, 널 label 방지
# ==================================================
@router.get("/weekly")
async def get_weekly_stats(user_id: str = Depends(get_current_user_id)):
    try:
        start_date = datetime.utcnow() - timedelta(weeks=5)

        pipeline = [
            {"$match": {
                "user_id": user_id,
                "created_at": {"$gte": start_date}
            }},
            {"$set": {
                "weekStart": {
                    "$dateTrunc": {
                        "date": "$created_at",
                        "unit": "week",
                        "timezone": TZ
                    }
                },
                "emoLabel": {"$ifNull": ["$analyzed_emotion.label", "중립"]},
            }},
            {"$group": {
                "_id": {"weekStart": "$weekStart", "emotion": "$emoLabel"},
                "count": {"$sum": 1},
                "avg_score": {"$avg": "$score"}
            }},
            {"$project": {
                "_id": 0,
                "week": {
                    "$concat": [
                        {"$dateToString": {"format": "%m/%d", "date": "$_id.weekStart", "timezone": TZ}},
                        " ~ ",
                        {"$dateToString": {
                            "format": "%m/%d",
                            "date": {"$dateAdd": {"startDate": "$_id.weekStart", "unit": "day", "amount": 6}},
                            "timezone": TZ
                        }}
                    ]
                },
                "label": "$_id.emotion",
                "count": 1,
                "avg_score": {"$round": ["$avg_score", 2]}
            }},
            {"$sort": {"week": 1}}
        ]

        result = await db["diaries"].aggregate(pipeline).to_list(None)
        return {"weekly": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주간 통계 오류: {str(e)}")


# ==================================================
# ✅ 최근 3개월 월간 통계 (라벨: YYYY-MM)
#    - analyzed_emotion.label 기준 빈도 + 평균 score
# ==================================================
@router.get("/monthly")
async def get_monthly_stats(user_id: str = Depends(get_current_user_id)):
    try:
        start_date = datetime.utcnow() - timedelta(days=90)

        pipeline = [
            {"$match": {
                "user_id": user_id,
                "created_at": {"$gte": start_date}
            }},
            {"$set": {
                "emoLabel": {"$ifNull": ["$analyzed_emotion.label", "중립"]},
                "month": {"$dateToString": {"format": "%Y-%m", "date": "$created_at", "timezone": TZ}}
            }},
            {"$group": {
                "_id": {"month": "$month", "emotion": "$emoLabel"},
                "count": {"$sum": 1},
                "avg_score": {"$avg": "$score"}
            }},
            {"$project": {
                "_id": 0,
                "month": "$_id.month",
                "label": "$_id.emotion",
                "count": 1,
                "avg_score": {"$round": ["$avg_score", 2]}
            }},
            {"$sort": {"month": 1}}
        ]

        result = await db["diaries"].aggregate(pipeline).to_list(None)
        return {"monthly": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"월간 통계 오류: {str(e)}")


# ==================================================
# ✅ (NEW) 최근 30일 위험도 분포
#    - risk_level: none / moderate / high (없으면 none)
#    - 프론트 도넛/바 차트에 바로 사용
# ==================================================
@router.get("/risk")
async def get_risk_stats(user_id: str = Depends(get_current_user_id)):
    try:
        start_date = datetime.utcnow() - timedelta(days=30)

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
            }},
            {"$addFields": {
                "order": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$risk_level", "high"]}, "then": 0},
                            {"case": {"$eq": ["$risk_level", "moderate"]}, "then": 1},
                            {"case": {"$eq": ["$risk_level", "low"]}, "then": 2},
                            {"case": {"$eq": ["$risk_level", "none"]}, "then": 3},
                        ],
                        "default": 4
                    }
                }
            }},
            {"$sort": {"order": 1}}
        ]

        data = await db["diaries"].aggregate(pipeline).to_list(None)

        # 누락 레벨 보정(0 채워 넣기) — 차트용
        base = {"none": 0, "low": 0, "moderate": 0, "high": 0}
        for r in data:
            rl = (r.get("risk_level") or "none").lower()
            if rl in base:
                base[rl] = r.get("count", 0)

        # 응답
        return {
            "since": start_date.isoformat(),
            "summary": [{"risk_level": k, "count": v} for k, v in base.items()]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"위험도 통계 오류: {str(e)}")
