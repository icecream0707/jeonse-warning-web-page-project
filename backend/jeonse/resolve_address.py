from dataclasses import dataclass


@dataclass(frozen=True)
class AddressResult:
    status: str
    key: tuple | None = None
    candidates: tuple = ()
    name: str = ""  # status가 ok일 때 건물명. 지번이 안 맞을 때 이름으로 찾는 데 쓴다.


def _key(item):
    jibun = item["lnbrMnnm"]
    if item["lnbrSlno"] != "0":
        jibun += "-" + item["lnbrSlno"]
    return (item["admCd"][:5], item["emdNm"], jibun)


def resolve_address(items):
    if not items:
        return AddressResult("not_found")
    # 아파트 → 서울 → 산 아님 순으로 걸러서, 막다른 후보를 사용자에게 보이지 않는다.
    apartments = [i for i in items if i["bdKdcd"] == "1"]
    if not apartments:
        return AddressResult("not_apartment")
    seoul = [i for i in apartments if i["admCd"].startswith("11")]
    if not seoul:
        return AddressResult("not_seoul")
    usable = [i for i in seoul if i["mtYn"] != "1"]
    if not usable:
        return AddressResult("mountain")
    if len(usable) > 1:
        return AddressResult(
            "choose", candidates=tuple((i["bdNm"], _key(i)) for i in usable)
        )
    return AddressResult("ok", _key(usable[0]), name=usable[0]["bdNm"])
