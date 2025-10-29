import importlib.metadata as md
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.json_util import dumps
import certifi

def _ver(pkg: str) -> str:
    try:
        return md.version(pkg)
    except Exception:
        return "not-installed"

print("🔍 패키지 버전 확인 -----------------------------")
print("Python 환경 패키지 버전:")
print("  passlib =", _ver("passlib"))
print("  argon2-cffi =", _ver("argon2-cffi"))
print("  pymongo =", _ver("pymongo"))
print("  motor =", _ver("motor"))
print("  certifi =", _ver("certifi"))
print("  bcrypt =", _ver("bcrypt"))  # 있을 경우만, 없으면 not-installed
print("------------------------------------------------\n")

# Atlas URI (직접 비밀번호 넣기)
uri = "mongodb+srv://philip01100_db_user:<비밀번호>@cluster0.yu0h95r.mongodb.net/?retryWrites=true&w=majority"

print("🔍 MongoDB Atlas 연결 테스트 ---------------------")
try:
    client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())
    client.admin.command('ping')
    print("✅ MongoDB Atlas 연결 성공!")
    print("  Database:", client.list_database_names())
except Exception as e:
    print("❌ MongoDB 연결 실패:", e)

print("------------------------------------------------\n")
