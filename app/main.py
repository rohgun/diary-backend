from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
import os

# 라우터 임포트
from app.routes import auth, diary, stats
from app.auth.jwt import get_current_user_id
from app.routes.health import router as health_router

# MongoDB 연결 관련
from app.db.mongo import connect_to_mongo, close_mongo_connection


# -----------------------------------------------------
# 환경 변수 로드 (.env → 로컬 테스트 시)
# -----------------------------------------------------
load_dotenv()

# -----------------------------------------------------
# FastAPI 앱 초기화
# -----------------------------------------------------
app = FastAPI(title="Emotion Diary API")

# -----------------------------------------------------
# CORS 설정
# -----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중에는 * 허용, 배포 시에는 특정 도메인만!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------
# 라우터 등록
# -----------------------------------------------------
app.include_router(health_router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(diary.router, prefix="/diary", tags=["Diary"])
app.include_router(stats.router, prefix="/diary", tags=["Stats"])

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
@app.on_event("startup")
async def startup():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()


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
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # 모든 엔드포인트에 기본 BearerAuth 적용
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
