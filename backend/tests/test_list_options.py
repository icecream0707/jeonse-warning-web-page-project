from datetime import date

from jeonse.list_options import list_options
from jeonse.parse_trade import Trade
from jeonse.store import open_db, save_trades

KEY = ("11710", "잠실동", "22")


def trade(area, dong=None, day=1, amount=100000):
    return Trade(key=KEY, amount=amount, area=area, deal_date=date(2025, 8, day),
                 dong=dong, apt_name="리센츠", floor=day)


def conn_with(trades):
    conn = open_db(":memory:")
    save_trades(conn, trades)
    return conn


def test_areas_within_one_square_meter_are_grouped_under_the_most_common_value():
    conn = conn_with([trade(84.99, day=1), trade(84.99, day=2), trade(85.0, day=3),
                      trade(27.68, day=4), trade(59.9, day=5)])
    assert list_options(conn, KEY).areas == [(27.68, 1), (59.9, 1), (84.99, 3)]


def test_dongs_are_listed_in_numeric_order_when_two_or_more_exist():
    conn = conn_with([trade(84.99, "248", 1), trade(84.99, "201", 2),
                      trade(84.99, "9", 3), trade(84.99, None, 4)])
    assert list_options(conn, KEY).dongs == ["9", "201", "248"]


def test_no_dong_choice_when_fewer_than_two_real_dongs():
    conn = conn_with([trade(84.99, "201", 1), trade(84.99, "201", 2), trade(84.99, None, 3)])
    assert list_options(conn, KEY).dongs == []
