# app/services/resource.py
from typing import Dict, List, Any

# ==================================================
# ✅ 위험 수준별 기본 리소스
# ==================================================
BASE_RESOURCES: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "high": {
        "hotlines": [
            {"label": "자살예방상담 1393 (24시간)", "tel": "1393"},
            {"label": "정신건강위기상담 1588-9191", "tel": "1588-9191"},
        ],
        "links": [
            {"label": "국가트라우마센터", "url": "https://www.nct.go.kr"},
            {"label": "마음건강 길라잡이", "url": "https://www.mentalhealth.go.kr"},
        ],
        "quick_calm": [
            {"label": "당장 주변 사람에게 전화하기", "url": ""},
            {"label": "4-7-8 호흡 3회", "url": "https://www.youtube.com/results?search_query=4-7-8+breathing"},
        ],
    },
    "moderate": {
        "hotlines": [
            {"label": "정신건강상담전화", "tel": "1577-0199"},
        ],
        "links": [
            {"label": "웰니스 자료 모음", "url": "https://www.mentalhealth.go.kr"},
        ],
        "quick_calm": [
            {"label": "5분 마음챙김 명상", "url": "https://www.youtube.com/results?search_query=5min+mindfulness"},
            {"label": "가벼운 산책 10분", "url": ""},
        ],
    },
    "none": {
        "hotlines": [],
        "links": [],
        "quick_calm": [
            {"label": "짧은 스트레칭으로 마무리하기", "url": ""},
        ],
    },
}

# ==================================================
# ✅ 섹션 형태(dict of lists)로 반환
# ==================================================
def get_resources(risk_level: str) -> Dict[str, List[Dict[str, str]]]:
    """
    위험 수준(risk_level)에 맞는 섹션형 리소스를 반환.
    - hotlines / links / quick_calm 세 섹션을 dict로 반환
    """
    level = (risk_level or "none").lower()
    return BASE_RESOURCES.get(level, BASE_RESOURCES["none"])

# ==================================================
# ✅ 일기 API 스키마용: 하나의 리스트로 평탄화
# ==================================================
def get_safety_resources(risk_level: str = "none") -> List[Dict[str, Any]]:
    """
    DiaryResponse.risk_resources (List[dict])에 바로 들어갈 형태로
    섹션들을 하나의 리스트로 합쳐서 반환.
    """
    base = get_resources(risk_level)
    return base.get("hotlines", []) + base.get("links", []) + base.get("quick_calm", [])
