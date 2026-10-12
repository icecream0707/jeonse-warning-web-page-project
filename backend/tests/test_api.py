import io
import json
import os
from datetime import date, timedelta

import pytest

os.environ.setdefault("JUSO_KEY", "test-key")  # app을 가져올 때 읽는다. 실제 주소 API는 부르지 않는다.

from fastapi.testclient import TestClient  # noqa: E402

import app as app_module  # noqa: E402
from jeonse.config import DATA_EXTRACTED_AT  # noqa: E402
from jeonse.parse_trade import Trade  # noqa: E402
from jeonse.store import open_db, save_trades  # noqa: E402

KEY = ("11710", "잠실동", "22")


def trade(amount, days_ago, dong=None):
    return Trade(key=KEY, amount=amount, area=84.99, deal_date=date.today() - timedelta(days=days_ago),
                 dong=dong, apt_name="리센츠", floor=days_ago)


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    conn = open_db(db)
    save_trades(conn, [trade(100000, 10, "201"), trade(120000, 20, "202"), trade(140000, 30)])
    conn.close()
    monkeypatch.setattr(app_module, "DB_PATH", db)
    return TestClient(app_module.app)


def diagnose_body(**over):
    body = {"sgg": "11710", "umd": "잠실동", "jibun": "22", "area": 84.99, "dong": None, "deposit": 90000}
    return {**body, **over}


def test_diagnose_returns_ratio_and_the_data_extraction_date(client):
    r = client.post("/api/diagnose", json=diagnose_body())
    assert r.status_code == 200
    data = r.json()
    assert (data["status"], data["median"], data["level"]) == ("ok", 120000, "빠듯함")
    assert data["data_extracted_at"] == DATA_EXTRACTED_AT


@pytest.mark.parametrize("over", [{"deposit": 0}, {"deposit": -5}, {"area": 0}])
def test_diagnose_rejects_non_positive_numbers(client, over):
    assert client.post("/api/diagnose", json=diagnose_body(**over)).status_code == 422


def test_options_lists_areas_and_dongs(client):
    r = client.get("/api/options", params={"sgg": "11710", "umd": "잠실동", "jibun": "22"})
    assert r.json() == {"areas": [[84.99, 3]], "dongs": ["201", "202"]}


def test_built_frontend_is_served_at_root_without_hiding_the_api(tmp_path):
    from fastapi import FastAPI

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>전세 위험 진단</html>", encoding="utf-8")
    api = FastAPI()

    @api.get("/api/ping")
    def ping():
        return {"ok": True}

    app_module.mount_frontend(api, dist)
    c = TestClient(api)
    assert "전세 위험 진단" in c.get("/").text
    assert c.get("/api/ping").json() == {"ok": True}


def test_mount_frontend_is_skipped_when_dist_is_missing(tmp_path):
    from fastapi import FastAPI

    api = FastAPI()
    app_module.mount_frontend(api, tmp_path / "no-dist")  # 개발 중에는 Vite가 화면을 서빙한다
    assert TestClient(api).get("/").status_code == 404


def juso_item(name, jibun_main):
    return {"admCd": "1171010100", "emdNm": "잠실동", "lnbrMnnm": jibun_main, "lnbrSlno": "0",
            "mtYn": "0", "bdKdcd": "1", "bdNm": name}


def fake_juso(monkeypatch, items):
    payload = {"results": {"common": {"errorCode": "0", "errorMessage": "정상"}, "juso": items}}
    monkeypatch.setattr(app_module.urllib.request, "urlopen",
                        lambda url, timeout=None: io.BytesIO(json.dumps(payload).encode()))


def test_address_drops_candidates_without_trades_and_unwraps_a_single_one(client, monkeypatch):
    fake_juso(monkeypatch, [juso_item("리센츠", "22"), juso_item("거래없는빌라", "999")])
    data = client.get("/api/address", params={"q": "리센츠"}).json()
    assert (data["status"], data["key"]) == ("ok", list(KEY))


def test_address_with_a_different_jibun_is_matched_by_name(client, monkeypatch):
    fake_juso(monkeypatch, [juso_item("리센츠", "23")])  # 주소 API는 23, 실거래가는 22
    data = client.get("/api/address", params={"q": "리센츠"}).json()
    assert (data["status"], data["key"]) == ("ok", list(KEY))


def test_address_with_no_name_or_jibun_match_is_no_data_even_for_a_single_result(client, monkeypatch):
    fake_juso(monkeypatch, [juso_item("전혀다른단지", "777")])
    assert client.get("/api/address", params={"q": "다른"}).json()["status"] == "no_data"


def test_address_with_no_candidate_in_database_is_no_data(client, monkeypatch):
    fake_juso(monkeypatch, [juso_item("빌라A", "998"), juso_item("빌라B", "999")])
    assert client.get("/api/address", params={"q": "빌라"}).json()["status"] == "no_data"
