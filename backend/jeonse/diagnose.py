from dataclasses import dataclass
from datetime import timedelta
from statistics import median

MIN_TRADES = 3
AREA_TOLERANCE = 1.0  # ㎡
# shortcut: 12/24개월을 365/730일로 근사, 달력 기준이 필요해지면 교체
RECENT_DAYS = 365  # "최근 12개월"의 유일한 정의. 동 단계, 동별 중앙값, 단지 12개월이 모두 이걸 쓴다.
LONG_DAYS = 730
STAGES = (("complex_12m", RECENT_DAYS), ("complex_24m", LONG_DAYS))


@dataclass(frozen=True)
class Diagnosis:
    status: str
    basis: str | None = None
    count: int = 0
    min: int | None = None
    median: float | None = None
    max: int | None = None
    ratio: float | None = None
    level: str | None = None


def _same_complex_and_area(trades, key, area):
    return [t for t in trades if t.key == key and abs(t.area - area) <= AREA_TOLERANCE]


def dong_medians(trades, key, area, today):
    """동 모름일 때 동별 비교용: [(동, 건수, 중앙값)] 12개월, 동 번호순."""
    window = timedelta(days=RECENT_DAYS)
    by_dong = {}
    for t in _same_complex_and_area(trades, key, area):
        if t.dong and timedelta(0) <= today - t.deal_date <= window:
            by_dong.setdefault(t.dong, []).append(t.amount)
    ordered = sorted(by_dong, key=lambda d: (not d.isdigit(), int(d) if d.isdigit() else 0, d))
    return [(d, len(by_dong[d]), median(by_dong[d])) for d in ordered]


def diagnose(trades, key, area, dong, deposit, today):
    same = _same_complex_and_area(trades, key, area)
    stages = (("dong_12m", RECENT_DAYS),) + STAGES if dong else STAGES
    amounts = []
    for basis, days in stages:
        window = timedelta(days=days)
        pool = [t for t in same if t.dong == dong] if basis == "dong_12m" else same
        amounts = [t.amount for t in pool if timedelta(0) <= today - t.deal_date <= window]
        if len(amounts) >= MIN_TRADES:
            m = median(amounts)
            return Diagnosis("ok", basis, len(amounts), min(amounts), m, max(amounts),
                             deposit / m, _level(deposit, m))
    return Diagnosis("insufficient", count=len(amounts))


def _level(deposit, median_amount):
    # 정수 비교: 부동소수점 때문에 70%/80% 경계가 어긋나지 않게 한다.
    if deposit * 10 < median_amount * 7:
        return "여유 있음"
    if deposit * 10 < median_amount * 8:
        return "빠듯함"
    return "위험"
