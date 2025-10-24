from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8, max_length=15)
    name: str = Field(..., min_length=1)
    email: EmailStr  # 이메일 형식 자동 검증

class UserLogin(BaseModel):
    user_id: str
    password: str

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