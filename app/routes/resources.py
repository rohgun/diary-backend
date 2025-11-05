# app/routes/resources.py
from fastapi import APIRouter

router = APIRouter(prefix="/resources", tags=["Resources"])

@router.get("/help")
async def help_resources():
    # 한국 기준 기본값. 지역별로 나누고 싶으면 Accept-Language 등으로 분기.
    return {
        "hotlines": [
            {"label":"자살예방상담 1393 (24시간)", "tel":"1393"},
            {"label":"정신건강위기 1588-9191", "tel":"1588-9191"},
        ],
        "links": [
            {"label":"국가트라우마센터", "url":"https://www.nct.go.kr"},
            {"label":"마음건강 길라잡이", "url":"https://www.mentalhealth.go.kr"},
        ],
        "quick_calm": [
            {"label":"4-7-8 호흡 3회", "url":"https://www.youtube.com/results?search_query=4-7-8+breathing"},
            {"label":"5분 마음챙김", "url":"https://www.youtube.com/results?search_query=5min+mindfulness"},
        ],
    }
