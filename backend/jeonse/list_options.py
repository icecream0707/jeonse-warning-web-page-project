from collections import Counter
from dataclasses import dataclass

from jeonse.diagnose import AREA_TOLERANCE
from jeonse.store import load_trades


@dataclass(frozen=True)
class Options:
    areas: list  # [(대표 면적, 거래 건수)] 오름차순
    dongs: list  # 실제 동이 2개 이상일 때만 채운다


def list_options(conn, key):
    trades = load_trades(conn, key)
    counts = Counter(t.area for t in trades)
    clusters = []
    for area in sorted(counts):
        # shortcut: 바로 앞 면적과 오차 안이면 같은 평형(체인). 면적이 촘촘히 이어지는 단지는 넓게 묶일 수 있음.
        if clusters and area - clusters[-1][0] <= AREA_TOLERANCE:
            clusters[-1].append(area)
        else:
            clusters.append([area])
    areas = [
        (max(c, key=lambda a: (counts[a], -a)), sum(counts[a] for a in c)) for c in clusters
    ]
    dongs = {t.dong for t in trades if t.dong}
    if len(dongs) < 2:
        dongs = set()
    return Options(areas, sorted(dongs, key=lambda d: (not d.isdigit(), int(d) if d.isdigit() else 0, d)))
