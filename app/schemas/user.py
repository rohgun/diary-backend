# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, field_validator

# 공통: bcrypt는 UTF-8 기준 72바이트 초과 불가
def _check_bcrypt_limit(pw: str) -> str:
    if len(pw.encode("utf-8")) > 72:
        raise ValueError("비밀번호는 72바이트(UTF-8 기준)를 넘을 수 없습니다.")
    return pw

class UserCreate(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8, max_length=15)
    name: str = Field(..., min_length=1)
    email: EmailStr

    # pydantic v2용 필드 검증기
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _check_bcrypt_limit(v)

    # OpenAPI 예시
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "philip0110",
                "password": "myStrongPass123",
                "name": "Philip",
                "email": "philip0110@example.com"
            }
        }
    }

class UserLogin(BaseModel):
    user_id: str
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "philip0110",
                "password": "myStrongPass123"
            }
        }
    }

class UserResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr

class TokenUserResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    name: str
    email: EmailStr
