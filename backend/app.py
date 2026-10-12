"""전세 위험 진단 API. 실행: python -m uvicorn app:app --reload (backend 폴더에서)."""
import json
import urllib.parse
import urllib.request
from contextlib import asynccontextmanager, closing
from dataclasses import asdict
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from jeonse.config import DATA_EXTRACTED_AT, DB_PATH, FRONTEND_DIST, read_secret
from jeonse.diagnose import diagnose, dong_medians
from jeonse.list_options import list_options
from jeonse.match_complex import match_complex
from jeonse.resolve_address import resolve_address
from jeonse.store import load_trades, open_db

JUSO_URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
JUSO_KEY = read_secret("JUSO_KEY")


@asynccontextmanager
async def lifespan(_):
    # 파일이 없으면 sqlite가 빈 DB를 조용히 만들어 버리므로, 시작할 때 막는다.
    if not DB_PATH.exists():
        raise RuntimeError(f"DB 파일이 없습니다: {DB_PATH}. 먼저 python load_trades.py 를 실행하세요.")
    yield


app = FastAPI(lifespan=lifespan)


def db():
    return closing(open_db(DB_PATH))


@app.get("/api/address")
def address(q: str = Query(min_length=2, max_length=100)):
    query = urllib.parse.urlencode({
        "confmKey": JUSO_KEY, "currentPage": 1, "countPerPage": 100,
        "keyword": q, "resultType": "json"})
    try:
        with urllib.request.urlopen(f"{JUSO_URL}?{query}", timeout=10) as res:
            body = json.load(res)["results"]
    except Exception as e:  # URL(키 포함)이 응답에 새지 않게 한다
        raise HTTPException(502, f"주소 검색 실패: {type(e).__name__}")
    if body["common"]["errorCode"] != "0":
        raise HTTPException(502, f"주소 검색 오류: {body['common']['errorMessage']}")
    items = [{k: str(v).strip() for k, v in j.items()} for j in body.get("juso", [])]
    result = resolve_address(items)
    if result.status not in ("ok", "choose"):
        return {"status": result.status, "key": None, "candidates": []}
    found = [(result.name, result.key)] if result.status == "ok" else result.candidates
    # 지번이 다르면 이름으로 찾고, 우리 DB에 거래가 없는 후보(빌라 등)와 중복은 버려서
    # 막다른 선택지를 없앤다.
    unique = {}
    with db() as conn:
        for name, key in found:
            for matched in match_complex(conn, key, name):
                unique.setdefault(matched, name)
    candidates = tuple((name, key) for key, name in unique.items())
    if len(candidates) == 1:
        return {"status": "ok", "key": candidates[0][1], "candidates": []}
    if not candidates:
        return {"status": "no_data", "key": None, "candidates": []}
    return {"status": "choose", "key": None, "candidates": candidates}


@app.get("/api/options")
def options(sgg: str, umd: str, jibun: str):
    with db() as conn:
        o = list_options(conn, (sgg, umd, jibun))
    return {"areas": o.areas, "dongs": o.dongs}


class DiagnoseIn(BaseModel):
    sgg: str
    umd: str
    jibun: str
    area: float = Field(gt=0)
    dong: str | None = None
    deposit: int = Field(gt=0, description="보증금, 만원")


@app.post("/api/diagnose")
def diagnose_endpoint(body: DiagnoseIn):
    key = (body.sgg, body.umd, body.jibun)
    with db() as conn:
        trades = load_trades(conn, key)
    today = date.today()
    result = asdict(diagnose(trades, key, body.area, body.dong, body.deposit, today))
    # 동을 모를 때만 동별 중앙값을 같이 준다.
    result["dong_medians"] = [] if body.dong else dong_medians(trades, key, body.area, today)
    result["data_extracted_at"] = DATA_EXTRACTED_AT
    return result


def mount_frontend(application, dist):
    # API 경로를 다 등록한 뒤에 "/"를 마운트해야 /api가 가려지지 않는다.
    if dist.exists():
        application.mount("/", StaticFiles(directory=dist, html=True), name="frontend")


mount_frontend(app, FRONTEND_DIST)
