import sqlite3
from datetime import date

from jeonse.parse_trade import Trade

# dong은 NULL을 같은 값으로 취급하려고 빈 문자열로 저장한다(UNIQUE가 NULL을 서로 다르게 보기 때문).
SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    sgg TEXT NOT NULL, umd TEXT NOT NULL, jibun TEXT NOT NULL,
    apt_name TEXT NOT NULL, dong TEXT NOT NULL,
    area REAL NOT NULL, amount INTEGER NOT NULL, deal_date TEXT NOT NULL, floor INTEGER NOT NULL,
    UNIQUE (sgg, umd, jibun, dong, area, amount, deal_date, floor)
)
"""


def open_db(path):
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    return conn


def _insert(conn, trades):
    conn.executemany(
        "INSERT OR IGNORE INTO trades VALUES (?,?,?,?,?,?,?,?,?)",
        [(*t.key, t.apt_name, t.dong or "", t.area, t.amount, t.deal_date.isoformat(), t.floor)
         for t in trades],
    )


def save_trades(conn, trades):
    with conn:
        _insert(conn, trades)


def replace_month(conn, sgg, year_month, trades):
    """구·월 하나를 새 응답으로 통째로 바꾼다. 나중에 해제·정정된 거래가 남지 않게 한다."""
    month = f"{year_month[:4]}-{year_month[4:]}-%"
    with conn:  # 지우기와 넣기를 한 트랜잭션으로 묶어, 중간에 실패하면 원래대로 돌린다.
        conn.execute("DELETE FROM trades WHERE sgg=? AND deal_date LIKE ?", (sgg, month))
        _insert(conn, trades)


def has_trades(conn, key):
    return conn.execute(
        "SELECT 1 FROM trades WHERE sgg=? AND umd=? AND jibun=? LIMIT 1", key
    ).fetchone() is not None


def load_trades(conn, key):
    rows = conn.execute(
        "SELECT apt_name, dong, area, amount, deal_date, floor FROM trades "
        "WHERE sgg=? AND umd=? AND jibun=?", key)
    return [
        Trade(key=key, amount=amount, area=area, deal_date=date.fromisoformat(d),
              dong=dong or None, apt_name=name, floor=floor)
        for name, dong, area, amount, d, floor in rows
    ]
