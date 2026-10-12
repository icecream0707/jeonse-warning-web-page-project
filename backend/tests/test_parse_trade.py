from datetime import date

from jeonse.parse_trade import parse_trade

# 실제 API 응답(송파구 2024-09, 리센츠)에서 가져온 행. 값은 모두 문자열.
RECENTS = {
    "aptDong": "248", "aptNm": "리센츠", "dealAmount": "266,000",
    "dealYear": "2024", "dealMonth": "9", "dealDay": "27",
    "excluUseAr": "84.99", "floor": "8", "jibun": "22",
    "sggCd": "11710", "umdNm": "잠실동", "cdealType": " ", "cdealDay": " ",
}


def test_amount_comma_removed_to_number():
    assert parse_trade(RECENTS).amount == 266000


def test_complex_key_area_and_date_are_read():
    trade = parse_trade(RECENTS)
    assert trade.key == ("11710", "잠실동", "22")
    assert trade.area == 84.99
    assert trade.deal_date == date(2024, 9, 27)


def test_apt_name_and_floor_are_read():
    trade = parse_trade(RECENTS)
    assert trade.apt_name == "리센츠"
    assert trade.floor == 8


def test_numeric_dong_is_kept():
    assert parse_trade(RECENTS).dong == "248"


def test_blank_dong_is_unknown():
    assert parse_trade({**RECENTS, "aptDong": " "}).dong is None


def test_dong_equal_to_apt_name_means_no_dong():
    # 현대뜨레비앙처럼 동 칸에 단지명이 들어온 경우
    raw = {**RECENTS, "aptNm": "현대뜨레비앙", "aptDong": "현대뜨레비앙"}
    assert parse_trade(raw).dong is None


def test_cancelled_deal_is_dropped():
    cancelled = {**RECENTS, "cdealType": "O", "cdealDay": "24.10.02"}
    assert parse_trade(cancelled) is None
