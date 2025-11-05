# app/services/safety.py
from __future__ import annotations
import re
from typing import Literal

Risk = Literal["none", "mild", "moderate", "high"]

# 한글/영문 혼용 대비 간단 정규화
def _norm(s: str) -> str:
    s = (s or "").strip()
    # 공백 축약 + 소문자화
    s = re.sub(r"\s+", " ", s)
    return s.lower()

# 점수 → 위험도 보정 (감정 강도 기반)
def _score_to_risk(score: int) -> Risk:
    try:
        sc = int(score)
    except Exception:
        sc = 5
    if sc >= 9:
        return "high"
    if sc >= 7:
        return "moderate"
    if sc >= 5:
        return "mild"
    return "none"

# 키워드 기반 위험 탐지(백업 규칙)
HIGH_KWS = [
    "자살", "죽고 싶", "끝내고 싶", "없어지고 싶", "살기 싫", "그만 살고",
    "해치고 싶다", "손목", "베고 싶", "목숨", "극단적 선택"
]
MODERATE_KWS = [
    "너무 힘들", "지쳤", "무기력", "절망", "포기", "버티기 힘들", "괴로워",
    "살 맛이", "희망이 없", "울고 싶"
]
MILD_KWS = [
    "우울", "슬픔", "불안", "짜증", "걱정", "불편", "회의감", "공허"
]

def _kw_detect(text: str) -> Risk:
    t = _norm(text)
    # 우선순위: high → moderate → mild
    if any(kw in t for kw in HIGH_KWS):
        return "high"
    if any(kw in t for kw in MODERATE_KWS):
        return "moderate"
    if any(kw in t for kw in MILD_KWS):
        return "mild"
    return "none"

def _label_bias(label: str) -> Risk:
    # 모델 레이블이 강한 부정일 때 약간 가중
    lab = _norm(label)
    if any(k in lab for k in ["분노", "불안", "슬픔"]):
        return "mild"
    return "none"

def _merge(a: Risk, b: Risk) -> Risk:
    order = {"none": 0, "mild": 1, "moderate": 2, "high": 3}
    return a if order[a] >= order[b] else b

def evaluate_risk_level(text: str, label: str | None = None, score: int | None = 5) -> Risk:
    """
    모델 응답을 '정제'하는 위험도 평가.
    - 텍스트 키워드 백업 규칙
    - 감정 점수(강도) 가중
    - 감정 레이블(분노/불안/슬픔) 편향 가중
    반환값: "none" | "mild" | "moderate" | "high"
    """
    # 키워드 우선 (명시적 위험 문구가 최우선)
    kw = _kw_detect(text)
    if kw == "high":
        return "high"

    # 점수 기반
    sc = _score_to_risk(score or 5)

    # 레이블 기반 약한 가중
    lb = _label_bias(label or "")

    # 병합(가장 높은 위험도 유지)
    return _merge(kw, _merge(sc, lb))
