from fastapi import APIRouter, HTTPException, Depends
from app.schemas.user import UserCreate, UserLogin, TokenUserResponse, UserResponse
from app.models.user import (
    get_user_by_user_id,
    create_user,
    verify_user_credentials,
    get_user_by_email,   # ✅ 추가
)
from app.db.user_repository import delete_user
from app.auth.jwt import create_access_token, get_current_user_id
from datetime import timedelta
from pydantic import BaseModel
from app.models.user import get_user_by_name_and_email, update_user_password

router = APIRouter()
# ✅ 비밀번호 찾기 요청 모델
class FindPasswordRequest(BaseModel):
    name: str
    email: str
    new_password: str   # 사용자가 새 비밀번호 직접 입력

@router.post("/find-password", summary="비밀번호 재설정")
async def find_password(request: FindPasswordRequest):
    user = await get_user_by_name_and_email(request.name, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="해당 이름/이메일로 가입된 계정을 찾을 수 없습니다.")

    updated = await update_user_password(user["user_id"], request.new_password)
    if not updated:
        raise HTTPException(status_code=500, detail="비밀번호 변경 중 오류 발생")

    return {"message": "비밀번호가 성공적으로 재설정되었습니다."}

# ✅ 아이디 찾기 (이메일 기반)
class FindIdRequest(BaseModel):
    email: str

@router.post("/find-id", response_model=UserResponse, summary="아이디 찾기")
async def find_id(request: FindIdRequest):
    user = await get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="해당 이메일로 가입된 계정을 찾을 수 없습니다.")
    return UserResponse(
        user_id=user["user_id"],
        name=user["name"],
        email=user["email"]
    )

# ✅ 회원가입
@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    existing_user = await get_user_by_user_id(user.user_id)
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    await create_user(user.dict())
    return UserResponse(user_id=user.user_id, name=user.name, email=user.email)

# ✅ 로그인 & JWT 발급
@router.post("/login", response_model=TokenUserResponse)
async def login(user: UserLogin):
    matched_user = await verify_user_credentials(user.user_id, user.password)
    if not matched_user:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다.")

    access_token = create_access_token(
        matched_user,
        expires_delta=timedelta(minutes=60)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": matched_user["user_id"],
        "name": matched_user["name"],
        "email": matched_user["email"]
    }

# ✅ 회원 탈퇴
@router.delete("/delete-account", summary="회원 탈퇴", description="현재 로그인한 계정을 삭제합니다.")
async def delete_account(user_id: str = Depends(get_current_user_id)):
    try:
        deleted = await delete_user(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        return {"message": "회원 탈퇴가 완료되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회원 탈퇴 중 오류 발생: {str(e)}")

# ✅ 테스트용
@router.get("/test")
async def test():
    return {"message": "라우터 정상 작동 중!"}
