from bson import ObjectId
from app.db.mongo import db

# ✅ 컬렉션
user_collection = db["users"]
diary_collection = db["diaries"]  # 회원 탈퇴 시 일기도 같이 삭제

# ✅ 회원 삭제
async def delete_user(user_id: str) -> bool:
    """
    주어진 user_id 를 가진 사용자를 삭제합니다.
    - users 컬렉션에서 사용자 제거
    - diaries 컬렉션에서 해당 사용자의 모든 일기 제거
    """
    # users 컬렉션에서 유저 삭제
    result = await user_collection.delete_one({"user_id": user_id})

    # 관련된 diaries 전부 삭제
    await diary_collection.delete_many({"user_id": user_id})

    # 삭제 성공 여부 반환
    return result.deleted_count > 0
