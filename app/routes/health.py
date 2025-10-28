# app/routes/health.py
from fastapi import APIRouter
from app.db import db

router = APIRouter()

@router.get("/health/db")
async def check_db():
    try:
        await db.command("ping")
        return {"status": "ok", "message": "MongoDB 연결 정상"}
    except Exception as e:
        return {"status": "fail", "error": str(e)}
