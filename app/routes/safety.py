# app/routes/safety.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth.jwt import get_current_user_id
from app.models.safety import get_recent_risk_summary, get_high_risk_entries

router = APIRouter(prefix="/safety", tags=["Safety"])

# ==================================================
# ✅ 최근 위험도 통계 (30일 기본)
# ==================================================
@router.get("/summary")
async def get_risk_summary(user_id: str = Depends(get_current_user_id)):
    try:
        data = await get_recent_risk_summary(user_id)
        return {"summary": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"위험도 요약 오류: {str(e)}")

# ==================================================
# ✅ 최근 위험 일기 목록
# ==================================================
@router.get("/high-risk")
async def get_high_risk(user_id: str = Depends(get_current_user_id)):
    try:
        entries = await get_high_risk_entries(user_id)
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"위험 일기 조회 오류: {str(e)}")
