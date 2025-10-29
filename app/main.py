from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
import os
import importlib.metadata as md

# MongoDB 연결 관련
from app.db.mongo import connect_to_mongo, close_mongo_connection

# -----------------------------------------------------
# 환경 변수 로드
# -----------------------------------------------------
load_dotenv()

app = FastAPI(title="Emotion Diary API")

# -----------------------------------------------------
# CORS 설정
# -----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------
# 기본 라우트
# -----------------------------------------------------
@app.get("/")
async def root():
    return {"message": "🚀 FastAPI 서버 정상 작동 중!"}


@app.get("/ping")
async def ping():
    return {"pong": True}


# -----------------------------------------------------
# 서버 시작/종료 시 MongoDB 연결
# -----------------------------------------------------
def _ver(pkg: str) -> str:
    try:
        return md.version(pkg)
    except Exception:
        return "not-installed"

@app.on_event("startup")
async def startup():
    # <- 여기를 안전하게 출력하도록 교체
    print(
        "[versions]",
        "passlib=", _ver("passlib"),
        "argon2-cffi=", _ver("argon2-cffi"),
        # bcrypt는 이제 안 쓰므로 굳이 출력 안 해도 됩니다.
        # "bcrypt=", _ver("bcrypt"),
    )
    await connect_to_mongo()

    # ✅ 여기서 라우터를 import하고 등록하면 user.py가 이미 연결된 상태에서 로드됨
    from app.routes import auth, diary, stats
    from app.routes.health import router as health_router

    app.include_router(health_router, tags=["Health"])
    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(diary.router, prefix="/diary", tags=["Diary"])
    app.include_router(stats.router, prefix="/diary", tags=["Stats"])


@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()
    print("❎ MongoDB 연결 해제")


# -----------------------------------------------------
# Swagger (OpenAPI) JWT 인증 설정
# -----------------------------------------------------
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

    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
