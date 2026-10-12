from datetime import date

from jeonse.parse_trade import Trade
from jeonse.store import has_trades, load_trades, open_db, replace_month, save_trades

KEY = ("11710", "잠실동", "22")
A = Trade(key=KEY, amount=266000, area=84.99, deal_date=date(2024, 9, 27),
          dong="248", apt_name="리센츠", floor=8)
B = Trade(key=KEY, amount=260000, area=84.99, deal_date=date(2024, 9, 14),
          dong=None, apt_name="리센츠", floor=13)
OTHER = Trade(key=("11110", "무악동", "60"), amount=143500, area=114.931,
              deal_date=date(2024, 7, 17), dong="107", apt_name="인왕산아이파크", floor=1)


def test_saved_trades_are_loaded_back_by_complex_key():
    conn = open_db(":memory:")
    save_trades(conn, [A, B, OTHER])
    assert sorted(load_trades(conn, KEY), key=lambda t: t.amount) == [B, A]


def test_has_trades_tells_whether_the_complex_is_in_the_database():
    conn = open_db(":memory:")
    save_trades(conn, [A])
    assert has_trades(conn, KEY) is True
    assert has_trades(conn, ("11710", "잠실동", "304-14")) is False


def test_replace_month_drops_trades_missing_from_the_new_response():
    # A가 나중에 해제돼서 같은 구·월을 다시 받으면 B만 온다.
    conn = open_db(":memory:")
    save_trades(conn, [A, B, OTHER])
    replace_month(conn, "11710", "202409", [B])
    assert load_trades(conn, KEY) == [B]
    assert load_trades(conn, OTHER.key) == [OTHER]  # 다른 구·월은 그대로


def test_replace_month_keeps_other_months_of_the_same_district():
    august = Trade(key=KEY, amount=250000, area=84.99, deal_date=date(2024, 8, 30),
                   dong="201", apt_name="리센츠", floor=3)
    conn = open_db(":memory:")
    save_trades(conn, [A, august])
    replace_month(conn, "11710", "202409", [])
    assert load_trades(conn, KEY) == [august]


def test_saving_the_same_trade_twice_does_not_duplicate():
    conn = open_db(":memory:")
    save_trades(conn, [A])
    save_trades(conn, [A, B])
    assert len(load_trades(conn, KEY)) == 2
