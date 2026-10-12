from datetime import date

from jeonse.match_complex import match_complex
from jeonse.parse_trade import Trade
from jeonse.store import open_db, save_trades


def trade(key, apt_name, floor=1):
    return Trade(key=key, amount=100000, area=84.99, deal_date=date(2025, 8, 1),
                 dong=None, apt_name=apt_name, floor=floor)


def conn_with(*trades):
    conn = open_db(":memory:")
    save_trades(conn, list(trades))
    return conn


RECENTS = ("11710", "잠실동", "22")


def test_exact_key_with_trades_is_returned_as_is():
    conn = conn_with(trade(RECENTS, "리센츠"))
    assert match_complex(conn, RECENTS, "리센츠") == [RECENTS]


def test_when_jibun_differs_the_same_name_in_the_same_dong_is_found():
    # 주소 API는 지번 23, 실거래가는 22로 신고된 단지
    conn = conn_with(trade(RECENTS, "리센츠"))
    assert match_complex(conn, ("11710", "잠실동", "23"), "리센츠") == [RECENTS]


def test_spaces_apartment_suffix_and_case_are_ignored_in_names():
    conn = conn_with(trade(("11200", "행당동", "10"), "DMC자이1단지"))
    assert match_complex(conn, ("11200", "행당동", "11"), "dmc 자이1단지 아파트") == [("11200", "행당동", "10")]


def test_several_jibun_with_the_same_name_are_all_returned():
    a, b = ("11710", "잠실동", "22"), ("11710", "잠실동", "22-1")
    conn = conn_with(trade(a, "리센츠"), trade(b, "리센츠"))
    assert sorted(match_complex(conn, ("11710", "잠실동", "99"), "리센츠")) == [a, b]


def test_other_dong_or_other_name_is_not_matched():
    conn = conn_with(trade(RECENTS, "리센츠"), trade(("11710", "신천동", "7"), "리센츠"))
    assert match_complex(conn, ("11710", "잠실동", "23"), "트리지움") == []
    assert match_complex(conn, ("11710", "방이동", "23"), "리센츠") == []
