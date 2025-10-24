from fastapi import Header, HTTPException
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from typing import Dict, Any
from app.config import settings

# ✅ JWT 토큰 생성 함수
def create_access_token(
    user: Dict[str, Any],
    expires_delta: timedelta = timedelta(minutes=settings.access_token_expire_minutes)
):
    to_encode = {
        "sub": user["user_id"],  # MongoDB _id 대신 로그인 아이디 저장
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# ✅ 토큰 검증 함수 (Authorization 헤더 직접 사용)
async def get_current_user_id(authorization: str = Header(...)) -> str:
    try:
        print("📥 [DEBUG] 받은 Authorization:", authorization)

        # "Bearer <token>" 형식인지 확인
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="인증 방식이 올바르지 않습니다")

        # JWT 디코딩
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        print("📤 [DEBUG] 디코딩된 payload:", payload)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="토큰에 user_id 없음")

        return user_id

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다. 다시 로그인해주세요.")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않음")
