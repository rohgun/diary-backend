from fastapi import APIRouter
from app.db import client

router = APIRouter()

@router.get("/health/db")
async def health_db():
    await client.admin.command("ping")
    return {"ok": True}
