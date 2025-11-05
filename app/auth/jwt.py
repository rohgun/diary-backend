from fastapi import Header, HTTPException
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from datetime import datetime, timedelta
from typing import Dict, Any
from app.config import settings

# ✅ JWT 토큰 생성
def create_access_token(
    user: Dict[str, Any],
    expires_delta: timedelta = timedelta(minutes=settings.access_token_expire_minutes),
):
    uid = user.get("user_id")
    if not uid:
        raise ValueError("user_id 누락")

    to_encode = {
        "sub": uid,  # 로그인 아이디
        "exp": datetime.utcnow() + expires_delta,
        "iat": datetime.utcnow(),
        # "iss": "emotion-diary",
        # "aud": "emotion-diary-app",
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

# ✅ 토큰 검증 (Authorization 헤더)
async def get_current_user_id(authorization: str = Header(...)) -> str:
    try:
        # 개발용 로그는 운영에서 비활성화 권장
        # print("📥 [DEBUG] 받은 Authorization:", authorization)

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise HTTPException(
                status_code=401,
                detail="인증 방식이 올바르지 않습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            # options={"verify_aud": False},
            # audience="emotion-diary-app",
            # leeway=5,
        )
        # print("📤 [DEBUG] 디코딩된 payload:", payload)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="토큰에 user_id 없음",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="토큰이 만료되었습니다. 다시 로그인해주세요.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="토큰이 유효하지 않음",
            headers={"WWW-Authenticate": "Bearer"},
        )
