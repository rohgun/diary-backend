# app/db/mongo.py
import os
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")  # Render에서도 동일한 키로 설정
DB_NAME = os.getenv("MONGODB_DB", "diary")  # URI와 통일

client: AsyncIOMotorClient | None = None
db = None

def _assert_env():
    if not MONGO_URI:
        raise RuntimeError(
            "MONGO_URI 환경변수가 비었습니다. Render → Environment 탭에서 값을 확인하세요."
        )
    if "mongodb+srv://" not in MONGO_URI:
        raise RuntimeError(
            "Atlas SRV URI가 아닙니다. mongodb+srv:// 형태로 넣어주세요."
        )

async def connect_to_mongo():
    global client, db
    _assert_env()
    try:
        # certifi CA 번들 명시가 핵심
        client = AsyncIOMotorClient(
            MONGO_URI,
            tls=True,
            tlsCAFile=certifi.where(),
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=5000,
            uuidRepresentation="standard",
            # Optional: 연결 튜닝
            connectTimeoutMS=5000,
            socketTimeoutMS=20000,
            retryWrites=True,
        )

        # 서버 선택(핸드셰이크) 단계에서 빨리 실패하도록 ping 수행
        await client.admin.command("ping")

        db = client[DB_NAME]
        print(f"✅ MongoDB Atlas 연결 성공: DB={DB_NAME}, CA={certifi.where()}")
    except (ServerSelectionTimeoutError, ConfigurationError) as e:
        print("❌ MongoDB 연결 실패(ServerSelection):", str(e))
        print("   - 체크리스트:")
        print("     1) Atlas Network Access에 Render Outbound IP 또는 0.0.0.0/0 추가")
        print("     2) requirements.txt: motor/pymongo/dnspython/certifi 최신")
        print("     3) MONGO_URI 값 정확, 특수문자 인코딩, 공백/따옴표 없음")
        print("     4) tlsCAFile=certifi.where() 지정")
        raise
    except Exception as e:
        print("❌ MongoDB 연결 실패(기타):", str(e))
        raise

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("❎ MongoDB 연결 종료")
