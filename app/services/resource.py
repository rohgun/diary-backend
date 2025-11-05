# app/services/resource.py
from typing import Dict, List

BASE_RESOURCES: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "high": {
        "hotlines": [
            {"label": "자살예방상담 1393 (24시간)", "tel": "1393"},
            {"label": "정신건강위기 1588-9191", "tel": "1588-9191"},
        ],
        "links": [
            {"label": "국가트라우마센터", "url": "https://www.nct.go.kr"},
            {"label": "마음건강 길라잡이", "url": "https://www.mentalhealth.go.kr"},
        ],
        "quick_calm": [
            {"label": "당장 주변 사람에게 전화", "url": ""},
            {"label": "4-7-8 호흡 3회", "url": "https://www.youtube.com/results?search_query=4-7-8+breathing"},
        ],
    },
    "moderate": {
        "hotlines": [{"label": "정신건강상담전화", "tel": "1577-0199"}],
        "links": [{"label": "웰니스 자료 모음", "url": "https://www.mentalhealth.go.kr"}],
        "quick_calm": [
            {"label": "5분 마음챙김", "url": "https://www.youtube.com/results?search_query=5min+mindfulness"},
            {"label": "가벼운 산책 10분", "url": ""},
        ],
    },
    "none": {
        "hotlines": [],
        "links": [],
        "quick_calm": [{"label": "짧은 스트레칭", "url": ""}],
    },
}

def get_resources(risk_level: str) -> Dict[str, List[Dict[str, str]]]:
    """
    위험 수준(risk_level)에 맞는 도움 리소스를 반환.
    """
    return BASE_RESOURCES.get(risk_level, BASE_RESOURCES["none"])
