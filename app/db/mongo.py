# app/db/mongo.py
import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGODB_DB", "emotion_diary")

client = None
db = None

async def connect_to_mongo():
    global client, db
    try:
        client = AsyncIOMotorClient(
            MONGO_URI,
             tls=True,                         # 명시
        tlsCAFile=certifi.where(), 
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=5000,
            uuidRepresentation="standard",
        )
        await client.admin.command("ping")
        db = client[DB_NAME]
        print(f"✅ MongoDB Atlas 연결 성공: {DB_NAME}")
    except Exception as e:
        print("❌ MongoDB 연결 실패:", str(e))
        raise e

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("❎ MongoDB 연결 종료")
