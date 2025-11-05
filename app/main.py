# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv
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
    allow_origins=["*"],   # 배포 시엔 필요한 도메인만 허용 권장
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
    # 패키지 버전 출력(디버깅용)
    print(
        "[versions]",
        "passlib=", _ver("passlib"),
        "argon2-cffi=", _ver("argon2-cffi"),
    )

    # DB 연결
    await connect_to_mongo()

    # ✅ 연결 이후 라우터 import & 등록 (의존 모듈들이 DB 초기화 후 로드되도록)
    from app.routes import auth, diary, stats, resources
    from app.routes.health import router as health_router
    from app.routes import safety
    

    app.include_router(health_router, tags=["Health"])
    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(diary.router, prefix="/diary", tags=["Diary"])
    app.include_router(stats.router)              # prefix는 /stats (routes 내부에서 지정)
    app.include_router(resources.router)          # prefix는 /resources (routes 내부에서 지정)
    app.include_router(safety.router)              # prefix는 /safety (routes 내부에서 지정)

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

    # 기본적으로 BearerAuth 적용 (원한다면 /health, /resources/help 등은 예외 처리 가능)
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
