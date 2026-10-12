from datetime import date

import pytest

from jeonse.diagnose import diagnose, dong_medians
from jeonse.parse_trade import Trade

KEY = ("11710", "잠실동", "22")
TODAY = date(2025, 10, 12)


def trade(amount, deal_date, area=84.99, dong=None, key=KEY):
    return Trade(key=key, amount=amount, area=area, deal_date=deal_date, dong=dong)


THREE_RECENT = [
    trade(100000, date(2025, 8, 1)),
    trade(120000, date(2025, 6, 1)),
    trade(140000, date(2025, 3, 1)),
]


@pytest.mark.parametrize(
    "deposit, level",
    [
        (83999, "여유 있음"),  # 69.99%
        (84000, "빠듯함"),  # 정확히 70%
        (95999, "빠듯함"),  # 79.99%
        (96000, "위험"),  # 정확히 80%
        (130000, "위험"),  # 100% 초과도 위험
    ],
)
def test_level_boundaries_at_70_and_80_percent(deposit, level):
    # 중앙값 120000 기준
    assert diagnose(THREE_RECENT, KEY, 84.99, None, deposit, TODAY).level == level


def test_other_complex_and_other_area_trades_are_ignored():
    noise = [
        trade(900000, date(2025, 8, 1), key=("11710", "잠실동", "304-14")),  # 다른 단지
        trade(900000, date(2025, 8, 1), area=59.0),  # 면적 차이 1㎡ 초과
    ]
    d = diagnose(THREE_RECENT + noise, KEY, 84.99, None, 90000, TODAY)
    assert (d.count, d.median) == (3, 120000)


def test_area_within_one_square_meter_is_included():
    near = trade(160000, date(2025, 9, 1), area=85.9)  # +0.91㎡
    d = diagnose(THREE_RECENT + [near], KEY, 84.99, None, 90000, TODAY)
    assert (d.count, d.median) == (4, 130000)  # (120000+140000)/2


def test_trade_older_than_12_months_is_not_used_when_enough_recent():
    old = trade(900000, date(2024, 8, 1))  # 14개월 전
    d = diagnose(THREE_RECENT + [old], KEY, 84.99, None, 90000, TODAY)
    assert (d.basis, d.count, d.median) == ("complex_12m", 3, 120000)


def test_expands_to_24_months_when_12_months_has_fewer_than_3():
    two_recent = THREE_RECENT[:2]  # 100000, 120000
    older = trade(140000, date(2024, 8, 1))  # 14개월 전
    d = diagnose(two_recent + [older], KEY, 84.99, None, 90000, TODAY)
    assert (d.status, d.basis, d.count, d.median) == ("ok", "complex_24m", 3, 120000)


def test_insufficient_when_even_24_months_has_fewer_than_3():
    d = diagnose(THREE_RECENT[:2], KEY, 84.99, None, 90000, TODAY)
    assert d.status == "insufficient"
    assert d.ratio is None and d.level is None


DONG_248 = [
    trade(250000, date(2025, 8, 1), dong="248"),
    trade(260000, date(2025, 5, 1), dong="248"),
    trade(270000, date(2025, 2, 1), dong="248"),
]
OTHER_DONGS = [trade(200000, date(2025, 8, 1), dong="220"), trade(210000, date(2025, 7, 1))]


def test_selected_dong_with_enough_trades_uses_only_that_dong():
    d = diagnose(DONG_248 + OTHER_DONGS, KEY, 84.99, "248", 200000, TODAY)
    assert (d.basis, d.count, d.median) == ("dong_12m", 3, 260000)


def test_selected_dong_with_too_few_trades_falls_back_to_complex():
    d = diagnose(DONG_248[:2] + OTHER_DONGS, KEY, 84.99, "248", 200000, TODAY)
    assert (d.basis, d.count, d.median) == ("complex_12m", 4, 230000)  # 200000,210000,250000,260000


def test_dong_not_selected_uses_whole_complex():
    d = diagnose(DONG_248 + OTHER_DONGS, KEY, 84.99, None, 200000, TODAY)
    assert (d.basis, d.count) == ("complex_12m", 5)


def test_dong_medians_lists_each_dong_in_the_12_month_window_for_the_area():
    trades = DONG_248 + OTHER_DONGS + [
        trade(900000, date(2024, 1, 1), dong="220"),  # 12개월 밖
        trade(900000, date(2025, 8, 1), area=59.0, dong="220"),  # 다른 면적
    ]
    assert dong_medians(trades, KEY, 84.99, TODAY) == [("220", 1, 200000), ("248", 3, 260000)]


def test_median_of_complex_12m_gives_ratio_and_level():
    d = diagnose(THREE_RECENT, KEY, 84.99, None, 90000, TODAY)
    assert d.status == "ok"
    assert d.basis == "complex_12m"
    assert (d.count, d.min, d.median, d.max) == (3, 100000, 120000, 140000)
    assert d.ratio == 0.75  # 90000 / 120000
    assert d.level == "빠듯함"
