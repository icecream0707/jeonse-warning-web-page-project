import re

from jeonse.store import has_trades


def _normalize(name):
    # 공백, 기호, "아파트" 표기 차이를 무시한다. 대소문자도 무시한다.
    return re.sub(r"[^0-9a-z가-힣]", "", name.lower().replace("아파트", ""))


def match_complex(conn, key, name):
    """주소 API의 단지 키가 실거래가의 지번과 다를 때, 같은 읍면동의 같은 이름으로 찾는다."""
    if has_trades(conn, key):
        return [key]
    sgg, umd, _ = key
    target = _normalize(name)
    rows = conn.execute(
        "SELECT DISTINCT jibun, apt_name FROM trades WHERE sgg=? AND umd=?", (sgg, umd))
    # shortcut: 이름이 정확히 같을 때만 맞춘다(부분 일치 없음). 실패가 많으면 부분 일치 추가.
    return sorted({(sgg, umd, jibun) for jibun, apt in rows if target and _normalize(apt) == target})
