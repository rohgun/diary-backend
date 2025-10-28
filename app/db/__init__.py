import os, certifi
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")  # 둘 다 지원
if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI (또는 MONGO_URI)가 설정되지 않았습니다.")

client = AsyncIOMotorClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000,
)

# URI에 /diary 가 들어있다면 그 DB가 기본으로 선택됩니다.
# 별도 지정하고 싶으면 아래처럼:
DB_NAME = os.getenv("MONGODB_DB") or "diary"
db = client[DB_NAME]
