from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Trade:
    key: tuple  # (sggCd, umdNm, jibun)
    amount: int  # 만원
    area: float  # 전용면적 ㎡
    deal_date: date
    dong: str | None  # None = 동 미상 또는 동 없음
    apt_name: str = ""
    floor: int = 0


def parse_trade(raw):
    if raw["cdealType"].strip() or raw["cdealDay"].strip():
        return None
    dong = raw["aptDong"].strip()
    if not dong or dong == raw["aptNm"].strip():
        dong = None
    return Trade(
        key=(raw["sggCd"], raw["umdNm"], raw["jibun"]),
        amount=int(raw["dealAmount"].replace(",", "")),
        area=float(raw["excluUseAr"]),
        deal_date=date(int(raw["dealYear"]), int(raw["dealMonth"]), int(raw["dealDay"])),
        dong=dong,
        apt_name=raw["aptNm"].strip(),
        floor=int(raw["floor"]),
    )
