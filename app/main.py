from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi  # ✅ 추가
from app.routes import auth, diary, stats
from app.auth.jwt import get_current_user_id
from app.db import client

app = FastAPI()

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중엔 * 허용, 운영 시 특정 도메인만
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 루트 라우트
@app.get("/")
async def root():
    return {"message": "FastAPI 서버 정상 작동 중!"}

# ✅ 테스트용 핑 라우트
@app.get("/ping")
async def ping():
    return {"pong": True}

# ✅ 라우터 등록
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(diary.router, prefix="/diary", tags=["Diary"])
app.include_router(stats.router, prefix="/diary", tags=["Stats"])

# ✅ Swagger UI에 Bearer 인증 방식 설정 (← 이것이 핵심!)
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

    # 모든 path에 Bearer 인증 적용
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi
# ✅ DB 헬스체크 라우트 추가
@app.get("/health/db", tags=["Health"])
async def health_db():
    await client.admin.command("ping")
    return {"ok": True}
