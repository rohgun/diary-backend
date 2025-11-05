# app/routes/diary.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import date as Date, datetime

from app.schemas.diary import DiaryCreate, DiaryResponse
from app.services.emotion_analysis import analyze_emotion
from app.auth.jwt import get_current_user_id

# ✅ 안전한 모듈 임포트 방식 (속성 누락 이슈 방지)
import app.models.diary as diary_model

router = APIRouter(tags=["Diary"])


# ==================================================
# ✅ 일기 저장 (AI 감정 분석 포함)
#   최종 경로: POST /diary/diary   (main에서 prefix="/diary" 이므로)
# ==================================================
@router.post("/diary", response_model=DiaryResponse)
async def create_diary_route(
    diary: DiaryCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        # 1) OpenAI 기반 감정 분석
        analysis = await analyze_emotion(diary.text)

        # 2) DB 저장 (risk_level, resource 포함)
        saved = await diary_model.create_diary(
            user_id=user_id,
            diary=diary,
            analyzed_emotion=analysis["analyzed_emotion"],
            reason=analysis.get("reason", ""),
            score=analysis.get("score", 5),
            feedback=analysis.get("feedback", ""),
            risk_level=analysis.get("risk_level", "none"),
            risk_resources=analysis.get("risk_resources"),
        )
        return saved

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 저장 중 오류 발생: {str(e)}")


# ==================================================
# ✅ 사용자 전체 일기 조회
#   최종 경로: GET /diary/diary
# ==================================================
@router.get("/diary", response_model=List[DiaryResponse])
async def get_user_diaries_route(user_id: str = Depends(get_current_user_id)):
    try:
        return await diary_model.get_user_diaries(user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 조회 중 오류 발생: {str(e)}")


# ==================================================
# ✅ 특정 날짜의 일기 조회 (YYYY-MM-DD)
#   최종 경로: GET /diary/diary/by-date/{target_date}
# ==================================================
@router.get("/diary/by-date/{target_date}", response_model=DiaryResponse)
async def get_diary_by_date_route(
    target_date: Date,
    user_id: str = Depends(get_current_user_id),
):
    try:
        target_dt = datetime.combine(target_date, datetime.min.time())
        diary = await diary_model.get_diary_by_date(user_id, target_dt)
        if not diary:
            raise HTTPException(status_code=404, detail="해당 날짜의 일기를 찾을 수 없습니다.")
        return diary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 조회 중 오류 발생: {str(e)}")


# ==================================================
# ✅ 단일 일기 조회 (id 기준)
#   최종 경로: GET /diary/diary/{diary_id}
# ==================================================
@router.get("/diary/{diary_id}", response_model=DiaryResponse)
async def get_diary_by_id_route(
    diary_id: str,
    user_id: str = Depends(get_current_user_id),
):
    diary = await diary_model.get_diary_by_id(user_id, diary_id)
    if not diary:
        raise HTTPException(status_code=404, detail="일기를 찾을 수 없습니다.")
    return diary


# ==================================================
# ✅ 일기 수정 (id 기준)
#   최종 경로: PUT /diary/diary/{diary_id}
# ==================================================
@router.put("/diary/{diary_id}", response_model=DiaryResponse)
async def update_diary_route(
    diary_id: str,
    diary: DiaryCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        updated = await diary_model.update_diary_by_id(user_id, diary_id, diary)
        if not updated:
            raise HTTPException(status_code=404, detail="수정할 일기를 찾을 수 없습니다.")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 수정 중 오류 발생: {str(e)}")


# ==================================================
# ✅ 일기 삭제 (id 기준)
#   최종 경로: DELETE /diary/diary/{diary_id}
# ==================================================
@router.delete("/diary/{diary_id}", summary="일기 삭제", description="특정 일기를 삭제합니다.")
async def delete_diary_route(
    diary_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        deleted = await diary_model.delete_diary_by_id(user_id, diary_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="일기를 찾을 수 없습니다.")
        return {"message": "일기가 성공적으로 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 삭제 중 오류 발생: {str(e)}")
