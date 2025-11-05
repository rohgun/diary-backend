# app/routes/diary.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import date as Date, datetime

from app.schemas.diary import DiaryCreate, DiaryResponse
from app.services.emotion_analysis import analyze_emotion
from app.auth.jwt import get_current_user_id
from app.models.diary import (
    create_diary,
    get_user_diaries,
    get_diary_by_date,
    get_diary_by_id,
    delete_diary_by_id,
    update_diary_by_id,
)

router = APIRouter(tags=["Diary"])


# ==================================================
# ✅ 일기 저장 (AI 감정 분석 포함)
# ==================================================
@router.post("/diary", response_model=DiaryResponse)
async def create_diary_route(
    diary: DiaryCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        # 1) OpenAI 기반 감정 분석
        analysis = await analyze_emotion(diary.text)
        # analysis 예시:
        # {
        #   "analyzed_emotion": {"label": "슬픔", "emoji": "😢"},
        #   "reason": "...",
        #   "score": 3,
        #   "feedback": "...",
        #   "risk_level": "none|watch|high"
        # }

        # 2) DB 저장
        # - models.create_diary()가 risk_level 파라미터를 받을 수 있게 업데이트 되어 있다면 함께 전달
        # - 아직 반영 전이면 TypeError가 나므로 폴백으로 risk_level 없이 호출
        risk_level = analysis.get("risk_level", "none")
        try:
            saved = await create_diary(
                user_id=user_id,
                diary=diary,
                analyzed_emotion=analysis["analyzed_emotion"],
                reason=analysis["reason"],
                score=analysis["score"],
                feedback=analysis["feedback"],
                risk_level=analysis.get("risk_level", "none"),
                risk_resources=analysis.get("resources"),  # 모델이 지원한다면 저장됨
            )
        except TypeError:
            # 구버전 시그니처 폴백
            saved = await create_diary(
                user_id=user_id,
                diary=diary,
                analyzed_emotion=analysis["analyzed_emotion"],
                reason=analysis["reason"],
                score=analysis["score"],
                feedback=analysis["feedback"],
            )

        return saved

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 저장 중 오류 발생: {str(e)}")


# ==================================================
# ✅ 사용자 전체 일기 조회
# ==================================================
@router.get("/diary", response_model=List[DiaryResponse])
async def get_user_diaries_route(
    user_id: str = Depends(get_current_user_id),
):
    try:
        return await get_user_diaries(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 조회 중 오류 발생: {str(e)}")


# ==================================================
# ✅ 특정 날짜의 일기 조회 (YYYY-MM-DD)
#   - path param은 date, 모델에는 datetime으로 변환
# ==================================================
@router.get("/diary/by-date/{target_date}", response_model=DiaryResponse)
async def get_diary_by_date_route(
    target_date: Date,
    user_id: str = Depends(get_current_user_id),
):
    try:
        target_dt = datetime.combine(target_date, datetime.min.time())
        diary = await get_diary_by_date(user_id, target_dt)
        if not diary:
            raise HTTPException(status_code=404, detail="해당 날짜의 일기를 찾을 수 없습니다.")
        return diary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 조회 중 오류 발생: {str(e)}")


# ==================================================
# ✅ 단일 일기 조회 (id 기준)
# ==================================================
@router.get("/diary/{diary_id}", response_model=DiaryResponse)
async def get_diary_by_id_route(
    diary_id: str,
    user_id: str = Depends(get_current_user_id),
):
    diary = await get_diary_by_id(user_id, diary_id)
    if not diary:
        raise HTTPException(status_code=404, detail="일기를 찾을 수 없습니다.")
    return diary


# ==================================================
# ✅ 일기 수정 (id 기준)
# ==================================================
@router.put("/diary/{diary_id}", response_model=DiaryResponse)
async def update_diary_route(
    diary_id: str,
    diary: DiaryCreate,
    user_id: str = Depends(get_current_user_id),
):
    try:
        updated = await update_diary_by_id(user_id, diary_id, diary)
        if not updated:
            raise HTTPException(status_code=404, detail="수정할 일기를 찾을 수 없습니다.")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 수정 중 오류 발생: {str(e)}")


# ==================================================
# ✅ 일기 삭제 (id 기준, 본인 것만)
# ==================================================
@router.delete("/diary/{diary_id}", summary="일기 삭제", description="특정 일기를 삭제합니다.")
async def delete_diary_route(
    diary_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        deleted = await delete_diary_by_id(user_id, diary_id)  # 본인 소유만 삭제
        if not deleted:
            raise HTTPException(status_code=404, detail="일기를 찾을 수 없습니다.")
        return {"message": "일기가 성공적으로 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일기 삭제 중 오류 발생: {str(e)}")
