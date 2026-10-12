"""서울 아파트 매매 실거래가를 받아 SQLite에 쌓는 수동 배치.

사용: python load_trades.py [--months 24] [--sgg 11110 ...] [--db data/jeonse.db]
키는 환경변수 DATA_GO_KR_KEY 또는 backend/.env 의 DATA_GO_KR_KEY=... 에서 읽는다.
"""
import argparse
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from jeonse.config import DB_PATH, read_secret
from jeonse.dong_check import DongRuleCheck
from jeonse.parse_response import parse_response
from jeonse.parse_trade import parse_trade
from jeonse.store import open_db, replace_month

URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
SEOUL_SGG = [
    "11110", "11140", "11170", "11200", "11215", "11230", "11260", "11290", "11305",
    "11320", "11350", "11380", "11410", "11440", "11470", "11500", "11530", "11545",
    "11560", "11590", "11620", "11650", "11680", "11710", "11740",
]
ROWS = 4000


def recent_months(n, today):
    y, m = today.year, today.month
    for _ in range(n):
        yield f"{y}{m:02d}"
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)


def fetch(key, sgg, ymd):
    query = urllib.parse.urlencode(
        {"serviceKey": key, "LAWD_CD": sgg, "DEAL_YMD": ymd, "pageNo": 1, "numOfRows": ROWS})
    with urllib.request.urlopen(f"{URL}?{query}", timeout=30) as res:
        items, total = parse_response(res.read().decode("utf-8"))
    if len(items) < total:  # 조용히 일부만 쌓지 않는다
        raise RuntimeError(f"{len(items)}건만 받음 (totalCount={total})")
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=24)
    ap.add_argument("--sgg", nargs="*", default=SEOUL_SGG)
    ap.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args()

    key = read_secret("DATA_GO_KR_KEY")
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    conn = open_db(args.db)
    failed = []
    dong_check = DongRuleCheck()
    for sgg in args.sgg:
        for ymd in recent_months(args.months, date.today()):
            try:
                items = fetch(key, sgg, ymd)
                trades = [t for t in map(parse_trade, items) if t]
                replace_month(conn, sgg, ymd, trades)
                for item in items:
                    dong_check.add(item)
                print(f"{sgg} {ymd}: {len(trades)}건")
            except Exception as e:  # URL(키 포함)이 출력되지 않게 메시지만 쓴다
                failed.append((sgg, ymd))
                print(f"{sgg} {ymd}: 실패 {type(e).__name__}: {e}")
    mixed = dong_check.mixed()
    print(f"동 규칙 점검: 단지명을 동으로 적은 거래와 실제 동이 섞인 단지 {len(mixed)}개")
    for (sgg, umd, jibun), name in mixed[:20]:
        print(f"  {sgg} {umd} {jibun} {name}")
    if failed:
        sys.exit(f"실패 {len(failed)}건: {failed[:5]}...")


if __name__ == "__main__":
    main()
