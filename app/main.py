# app/main.py (중요 부분만)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
import importlib.metadata as md

from app.db.mongo import connect_to_mongo, close_mongo_connection

load_dotenv()
app = FastAPI(title="Emotion Diary API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 배포 시엔 필요한 도메인만 허용 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "🚀 FastAPI 서버 정상 작동 중!"}

@app.get("/ping")
async def ping():
    return {"pong": True}

def _ver(pkg: str) -> str:
    try:
        return md.version(pkg)
    except Exception:
        return "not-installed"

@app.on_event("startup")
async def startup():
    print(
        "[versions]",
        "passlib=", _ver("passlib"),
        "argon2-cffi=", _ver("argon2-cffi"),
    )
    await connect_to_mongo()

    # ✅ DB 연결 이후 라우터 import & 등록
    from app.routes import auth, diary, stats, resources, safety
    from app.routes.health import router as health_router

    app.include_router(health_router, tags=["Health"])
    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(diary.router)              # ✅ prefix 없음 (파일 내부 prefix="/diary")
    app.include_router(stats.router)              # stats 파일 내부에 prefix="/stats"
    app.include_router(resources.router)          # resources 파일 내부에 prefix="/resources"
    app.include_router(safety.router)             # safety 파일 내부에 prefix="/safety"

@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()
    print("❎ MongoDB 연결 해제")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Emotion Diary API",
        version="1.0.0",
        description="감정일기 앱을 위한 OpenAPI 문서입니다",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }

    # ✅ 기본 Bearer 적용 + 공개 엔드포인트 예외
    public_paths = {"/", "/ping", "/resources/help", "/health"}
    for path, methods in openapi_schema["paths"].items():
        for method_obj in methods.values():
            method_obj.setdefault("security", [{"BearerAuth": []}])
        if path in public_paths:
            for method_obj in methods.values():
                method_obj["security"] = []

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
