from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.schemas.user import UserCreate, UserLogin, TokenUserResponse, UserResponse
from app.models.user import (
    get_user_by_user_id,
    create_user,
    verify_user_credentials,
    get_user_by_email,
    get_user_by_name_and_email,
    update_user_password,
    delete_user_by_id,
)
from app.auth.jwt import create_access_token, get_current_user_id

router = APIRouter()


# -------------------------------
# 비밀번호 찾기/재설정
# -------------------------------
class FindPasswordRequest(BaseModel):
    name: str
    email: str
    new_password: str  # 사용자가 새 비밀번호 직접 입력

@router.post("/find-password", summary="비밀번호 재설정")
async def find_password(request: FindPasswordRequest):
    user = await get_user_by_name_and_email(request.name, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="해당 이름/이메일로 가입된 계정을 찾을 수 없습니다.")

    try:
        updated = await update_user_password(user["user_id"], request.new_password)
    except ValueError as e:
        # bcrypt 72바이트 제한 등 사용자 입력 문제
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="비밀번호 변경 중 서버 오류가 발생했습니다.")

    if not updated:
        # 논리적 실패(수정 대상 없음 등)
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return {"message": "비밀번호가 성공적으로 재설정되었습니다."}


# -------------------------------
# 아이디 찾기 (이메일 기반)
# -------------------------------
class FindIdRequest(BaseModel):
    email: str

@router.post("/find-id", response_model=UserResponse, summary="아이디 찾기")
async def find_id(request: FindIdRequest):
    user = await get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="해당 이메일로 가입된 계정을 찾을 수 없습니다.")
    return UserResponse(user_id=user["user_id"], name=user["name"], email=user["email"])


# -------------------------------
# 회원가입
# -------------------------------
@router.post("/signup", response_model=UserResponse, summary="회원가입")
async def signup(user: UserCreate):
    # 아이디 중복 체크
    if await get_user_by_user_id(user.user_id):
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

    try:
        # pydantic v2: dict() 대신 model_dump()
        await create_user(user.model_dump())
    except ValueError as e:
        # bcrypt 72바이트 초과 등 입력 검증 에러
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="회원가입 처리 중 서버 오류가 발생했습니다.")

    return UserResponse(user_id=user.user_id, name=user.name, email=user.email)


# -------------------------------
# 로그인 & JWT 발급
# -------------------------------
@router.post("/login", response_model=TokenUserResponse, summary="로그인")
async def login(user: UserLogin):
    matched_user = await verify_user_credentials(user.user_id, user.password)
    if not matched_user:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다.")

    access_token = create_access_token(
        matched_user,  # 내부에서 user_id(subject) 등을 사용하도록 구현되어 있다고 가정
        expires_delta=timedelta(minutes=60),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": matched_user["user_id"],
        "name": matched_user["name"],
        "email": matched_user["email"],
    }


# -------------------------------
# 회원 탈퇴
# -------------------------------
@router.delete("/delete-account", summary="회원 탈퇴", description="현재 로그인한 계정을 삭제합니다.")
async def delete_account(user_id: str = Depends(get_current_user_id)):
    try:
        deleted = await delete_user_by_id(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return {"message": "회원 탈퇴가 완료되었습니다."}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="회원 탈퇴 중 서버 오류가 발생했습니다.")


# -------------------------------
# 테스트
# -------------------------------
@router.get("/test")
async def test():
    return {"message": "라우터 정상 작동 중!"}
