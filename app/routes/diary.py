# app/routes/diary.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.diary import DiaryCreate, DiaryResponse
from app.services.emotion_analysis import analyze_emotion
from app.auth.jwt import get_current_user_id
from app.models.diary import (
    create_diary,
    get_user_diaries,
    get_diary_by_date,
    get_diary_by_id,
    delete_diary_by_id,
)
from datetime import date

router = APIRouter(tags=["Diary"])


# ==================================================
# ✅ 일기 저장 (AI 감정 분석 포함)
# ==================================================
@router.post("/diary", response_model=DiaryResponse)
async def create_diary_route(
    diary: DiaryCreate,
    user_id: str = Depends(get_current_user_id)
):
    try:
        # OpenAI API 기반 감정 분석 실행
        analysis = await analyze_emotion(diary.text)

        # DB에 일기 저장
        return await create_diary(
            user_id=user_id,
            diary=diary,
            analyzed_emotion=analysis["analyzed_emotion"],
            reason=analysis["reason"],
            score=analysis["score"],
            feedback=analysis["feedback"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 저장 중 오류 발생: {str(e)}")


# ==================================================
# ✅ 사용자 전체 일기 조회
# ==================================================
@router.get("/diary", response_model=List[DiaryResponse])
async def get_user_diaries_route(
    user_id: str = Depends(get_current_user_id)
):
    try:
        diaries = await get_user_diaries(user_id)
        return diaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 조회 중 오류 발생: {str(e)}")


# ==================================================
# ✅ 특정 날짜의 일기 조회
# ==================================================
@router.get("/diary/by-date/{target_date}", response_model=DiaryResponse)
async def get_diary_by_date_route(
    target_date: date,
    user_id: str = Depends(get_current_user_id)
):
    diary = await get_diary_by_date(user_id, target_date)
    if not diary:
        raise HTTPException(status_code=404, detail="해당 날짜의 일기를 찾을 수 없습니다.")
    return diary


# ==================================================
# ✅ 단일 일기 조회 (id 기준)
# ==================================================
@router.get("/diary/{diary_id}", response_model=DiaryResponse)
async def get_diary_by_id_route(
    diary_id: str,
    user_id: str = Depends(get_current_user_id)
):
    diary = await get_diary_by_id(user_id, diary_id)
    if not diary:
        raise HTTPException(status_code=404, detail="일기를 찾을 수 없습니다.")
    return diary


# ==================================================
# ✅ 일기 삭제 (id 기준)
# ==================================================
@router.delete("/diary/{diary_id}", summary="일기 삭제", description="특정 일기를 삭제합니다.")
async def delete_diary_route(
    diary_id: str,
    user_id: str = Depends(get_current_user_id)
):
    try:
        deleted = await delete_diary_by_id(diary_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="일기를 찾을 수 없습니다.")
        return {"message": "일기가 성공적으로 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 삭제 중 오류 발생: {str(e)}")
