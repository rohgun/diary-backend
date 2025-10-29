from app.db.mongo import db
from passlib.context import CryptContext
from bson import ObjectId

# -------------------------------
# 전역 설정
# -------------------------------
# bcrypt → passlib context로만 관리 (직접 import 제거)
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
# 비밀번호 길이 검증
# -------------------------------
def validate_password_length(password: str):
    """
    bcrypt는 72바이트 이상 비밀번호를 지원하지 않음.
    """
    if len(password.encode("utf-8")) > 72:
        raise ValueError("비밀번호는 72바이트(UTF-8 기준)를 넘을 수 없습니다.")


# -------------------------------
# 사용자 생성
# -------------------------------
async def create_user(user_data: dict):
    """
    회원가입 시 새로운 사용자 생성
    """
    user_collection = get_user_collection()

    # 비밀번호 길이 제한 확인
    validate_password_length(user_data["password"])

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
    user_collection = get_user_collection()
    return await user_collection.find_one({"user_id": user_id})


# -------------------------------
# 로그인 검증
# -------------------------------
async def verify_user_credentials(user_id: str, password: str):
    user = await get_user_by_user_id(user_id)
    if user and verify_password(password, user["password"]):
        return user
    return None


# -------------------------------
# 이메일로 사용자 찾기
# -------------------------------
async def get_user_by_email(email: str):
    user_collection = get_user_collection()
    return await user_collection.find_one({"email": email})


# -------------------------------
# 이름 + 이메일로 사용자 찾기
# -------------------------------
async def get_user_by_name_and_email(name: str, email: str):
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

    # 길이 확인
    validate_password_length(new_password)

    hashed_pw = pwd_context.hash(new_password)
    result = await user_collection.update_one(
        {"user_id": user_id},
        {"$set": {"password": hashed_pw}},
    )
    return result.modified_count > 0


# -------------------------------
# 사용자 삭제 (선택)
# -------------------------------
async def delete_user_by_id(user_id: str):
    user_collection = get_user_collection()
    result = await user_collection.delete_one({"user_id": user_id})
    return result.deleted_count > 0


# -------------------------------
# 전체 사용자 조회 (관리용)
# -------------------------------
async def get_all_users():
    user_collection = get_user_collection()
    users = []
    async for user in user_collection.find():
        user["_id"] = str(user["_id"])
        users.append(user)
    return users
