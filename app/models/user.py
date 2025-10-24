from app.db.mongo import db
from passlib.context import CryptContext
from passlib.hash import bcrypt
user_collection = db["users"]
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 사용자 생성
async def create_user(user_data: dict):
    hashed_pw = pwd_context.hash(user_data["password"])
    user_data["password"] = hashed_pw

    result = await user_collection.insert_one({
        "user_id": user_data["user_id"],
        "password": user_data["password"],
        "name": user_data["name"],
        "email": user_data["email"]
    })
    return str(result.inserted_id)

# 비밀번호 검증
def verify_password(plain_pw: str, hashed_pw: str) -> bool:
    return pwd_context.verify(plain_pw, hashed_pw)

# 아이디로 사용자 조회
async def get_user_by_user_id(user_id: str):
    return await user_collection.find_one({"user_id": user_id})

# 로그인 검증
async def verify_user_credentials(user_id: str, password: str):
    user = await get_user_by_user_id(user_id)
    if user and verify_password(password, user["password"]):
        return user
    return None
# ✅ 이메일로 사용자 찾기
async def get_user_by_email(email: str):
    return await db["users"].find_one({"email": email})
# ✅ 이름 + 이메일로 사용자 조회
async def get_user_by_name_and_email(name: str, email: str):
    return await db["users"].find_one({"name": name, "email": email})

# ✅ 비밀번호 업데이트
async def update_user_password(user_id: str, new_password: str):
    hashed_pw = bcrypt.hash(new_password)
    result = await db["users"].update_one(
        {"user_id": user_id},
        {"$set": {"password": hashed_pw}}
    )
    return result.modified_count > 0
