from fastapi import APIRouter, Depends, HTTPException
from app.auth.jwt import get_current_user_id
from app.db.mongo import db
from datetime import datetime, timedelta

router = APIRouter(prefix="/stats", tags=["Stats"])

# ✅ 최근 5주 주간 통계 (라벨: "MM/DD ~ MM/DD")
@router.get("/weekly")
async def get_weekly_stats(user_id: str = Depends(get_current_user_id)):
    try:
        start_date = datetime.utcnow() - timedelta(weeks=5)

        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "startOfWeek": {
                            "$dateTrunc": {
                                "date": "$created_at",
                                "unit": "week",
                                "binSize": 1,
                                "timezone": "Asia/Seoul"
                            }
                        },
                        "emotion": "$analyzed_emotion.label"
                    },
                    "count": {"$sum": 1},
                    "avg_score": {"$avg": "$score"}
                }
            },
            {
                "$project": {
                    "week": {
                        "$concat": [
                            {"$dateToString": {"format": "%m/%d", "date": "$_id.startOfWeek", "timezone": "Asia/Seoul"}},
                            " ~ ",
                            {"$dateToString": {
                                "format": "%m/%d",
                                "date": {"$dateAdd": {"startDate": "$_id.startOfWeek", "unit": "day", "amount": 6}},
                                "timezone": "Asia/Seoul"
                            }}
                        ]
                    },
                    "label": "$_id.emotion",
                    "count": 1,
                    "avg_score": {"$round": ["$avg_score", 2]},
                    "_id": 0
                }
            },
            {"$sort": {"week": 1}}
        ]

        result = await db["diaries"].aggregate(pipeline).to_list(None)
        return {"weekly": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주간 통계 오류: {str(e)}")


# ✅ 최근 3개월 월간 통계 (라벨: YYYY-MM)
@router.get("/monthly")
async def get_monthly_stats(user_id: str = Depends(get_current_user_id)):
    try:
        start_date = datetime.utcnow() - timedelta(days=90)

        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "month": {"$dateToString": {"format": "%Y-%m", "date": "$created_at", "timezone": "Asia/Seoul"}},
                        "emotion": "$analyzed_emotion.label"
                    },
                    "count": {"$sum": 1},
                    "avg_score": {"$avg": "$score"}
                }
            },
            {
                "$project": {
                    "month": "$_id.month",
                    "label": "$_id.emotion",
                    "count": 1,
                    "avg_score": {"$round": ["$avg_score", 2]},
                    "_id": 0
                }
            },
            {"$sort": {"month": 1}}
        ]

        result = await db["diaries"].aggregate(pipeline).to_list(None)
        return {"monthly": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"월간 통계 오류: {str(e)}")
