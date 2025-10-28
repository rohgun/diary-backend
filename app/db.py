# app/db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()  # 로컬 테스트용, Render에서는 자동 주입됨

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGODB_DB", "diary")

client = None
db = None

async def connect_to_mongo():
    """
    앱 시작 시 MongoDB Atlas 연결
    """
    global client, db
    client = AsyncIOMotorClient(
        MONGO_URI,
        server_api=ServerApi('1'),
        serverSelectionTimeoutMS=5000,
        uuidRepresentation="standard",
    )
    # 연결 확인 (ping)
    await client.admin.command("ping")
    db = client[DB_NAME]
    print("✅ MongoDB Atlas 연결 성공")

async def close_mongo_connection():
    """
    앱 종료 시 연결 해제
    """
    global client
    if client:
        client.close()
        print("❎ MongoDB 연결 종료")
