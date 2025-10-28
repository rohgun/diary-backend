# app/models/user.py
from app.db.mongo import db
from passlib.context import CryptContext
from passlib.hash import bcrypt
from bson import ObjectId

# -------------------------------
# 전역 설정
# -------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------------
# 안전한 컬렉션 접근 함수
# -------------------------------
def get_user_collection():
    """
    MongoDB가 연결되기 전에 접근하면 오류 방지.
    FastAPI startup 이벤트에서 connect_to_mongo() 실행 후 사용해야 함.
    """
    if db is None:
        raise RuntimeError("❌ MongoDB 연결 전 상태입니다. connect_to_mongo()가 실행되었는지 확인하세요.")
    return db["users"]


# -------------------------------
# 사용자 생성
# -------------------------------
async def create_user(user_data: dict):
    """
    회원가입 시 새로운 사용자 생성
    """
    user_collection = get_user_collection()

    hashed_pw = pwd_context.hash(user_data["password"])
    user_data["password"] = hashed_pw

    result = await user_collection.insert_one({
        "user_id": user_data["user_id"],
        "password": user_data["password"],
        "name": user_data["name"],
        "email": user_data["email"],
    })

    return str(result.inserted_id)


# -------------------------------
# 비밀번호 검증
# -------------------------------
def verify_password(plain_pw: str, hashed_pw: str) -> bool:
    """
    사용자가 입력한 비밀번호와 DB에 저장된 해시 비교
    """
    return pwd_context.verify(plain_pw, hashed_pw)


# -------------------------------
# 아이디로 사용자 조회
# -------------------------------
async def get_user_by_user_id(user_id: str):
    """
    user_id로 사용자 찾기
    """
    user_collection = get_user_collection()
    return await user_collection.find_one({"user_id": user_id})


# -------------------------------
# 로그인 검증
# -------------------------------
async def verify_user_credentials(user_id: str, password: str):
    """
    로그인 시 사용자 검증
    """
    user = await get_user_by_user_id(user_id)
    if user and verify_password(password, user["password"]):
        return user
    return None


# -------------------------------
# 이메일로 사용자 찾기
# -------------------------------
async def get_user_by_email(email: str):
    """
    이메일로 사용자 찾기
    """
    user_collection = get_user_collection()
    return await user_collection.find_one({"email": email})


# -------------------------------
# 이름 + 이메일로 사용자 찾기
# -------------------------------
async def get_user_by_name_and_email(name: str, email: str):
    """
    이름 + 이메일 조합으로 사용자 찾기
    """
    user_collection = get_user_collection()
    return await user_collection.find_one({"name": name, "email": email})


# -------------------------------
# 비밀번호 업데이트
# -------------------------------
async def update_user_password(user_id: str, new_password: str):
    """
    비밀번호 재설정 (비밀번호 찾기 시)
    """
    user_collection = get_user_collection()

    hashed_pw = bcrypt.hash(new_password)
    result = await user_collection.update_one(
        {"user_id": user_id},
        {"$set": {"password": hashed_pw}},
    )
    return result.modified_count > 0


# -------------------------------
# 사용자 삭제 (확장 기능)
# -------------------------------
async def delete_user_by_id(user_id: str):
    """
    계정 삭제 기능 (선택)
    """
    user_collection = get_user_collection()
    result = await user_collection.delete_one({"user_id": user_id})
    return result.deleted_count > 0


# -------------------------------
# 전체 사용자 조회 (관리용)
# -------------------------------
async def get_all_users():
    """
    모든 사용자 목록 가져오기
    """
    user_collection = get_user_collection()
    users = []
    async for user in user_collection.find():
        user["_id"] = str(user["_id"])  # ObjectId → str 변환
        users.append(user)
    return users
