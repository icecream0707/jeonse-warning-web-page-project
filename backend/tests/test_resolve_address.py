from jeonse.resolve_address import resolve_address

# 실제 주소 검색 API 응답(리센츠, 리센츠 상가, 리센츠빌)에서 쓰는 필드만 뽑은 것. 값은 공백 제거된 문자열.
RECENTS = {
    "admCd": "1171010100", "emdNm": "잠실동", "lnbrMnnm": "22", "lnbrSlno": "0",
    "mtYn": "0", "bdKdcd": "1", "bdNm": "리센츠",
}


RECENTS_VILLE = {
    "admCd": "1171010100", "emdNm": "잠실동", "lnbrMnnm": "304", "lnbrSlno": "14",
    "mtYn": "0", "bdKdcd": "1", "bdNm": "리센츠빌",
}


PARK = {  # 광진구 어린이대공원: 공동주택 아님
    "admCd": "1121510200", "emdNm": "능동", "lnbrMnnm": "18", "lnbrSlno": "0",
    "mtYn": "0", "bdKdcd": "0", "bdNm": "어린이대공원",
}
SUWON = {  # 수원 자연앤자이: 아파트지만 서울 아님
    "admCd": "4111710300", "emdNm": "이의동", "lnbrMnnm": "1353", "lnbrSlno": "0",
    "mtYn": "0", "bdKdcd": "1", "bdNm": "자연앤자이",
}


def test_non_apartment_is_rejected():
    assert resolve_address([PARK]).status == "not_apartment"


def test_outside_seoul_is_rejected():
    assert resolve_address([SUWON]).status == "not_seoul"


def test_mountain_lot_is_rejected():
    assert resolve_address([{**RECENTS, "mtYn": "1"}]).status == "mountain"


RECENTS_SHOP = {  # 리센츠 상가: 지번 22-6, 공동주택 아님
    "admCd": "1171010100", "emdNm": "잠실동", "lnbrMnnm": "22", "lnbrSlno": "6",
    "mtYn": "0", "bdKdcd": "0", "bdNm": "리센츠",
}


def test_shop_is_ignored_when_apartment_also_matches():
    result = resolve_address([RECENTS, RECENTS_SHOP])
    assert result.status == "ok"
    assert result.key == ("11710", "잠실동", "22")


def test_several_apartments_ask_user_to_choose():
    result = resolve_address([RECENTS, RECENTS_SHOP, RECENTS_VILLE])
    assert result.status == "choose"
    assert result.candidates == (
        ("리센츠", ("11710", "잠실동", "22")),
        ("리센츠빌", ("11710", "잠실동", "304-14")),
    )


def test_non_seoul_candidates_are_dropped_before_choosing():
    assert resolve_address([SUWON, RECENTS]).key == ("11710", "잠실동", "22")
    result = resolve_address([SUWON, RECENTS, RECENTS_VILLE])
    assert result.status == "choose"
    assert [name for name, _ in result.candidates] == ["리센츠", "리센츠빌"]


def test_mountain_candidates_are_dropped_before_choosing():
    mountain = {**RECENTS_VILLE, "mtYn": "1"}
    assert resolve_address([RECENTS, mountain]).status == "ok"


def test_no_result_is_not_found():
    assert resolve_address([]).status == "not_found"


def test_ok_result_carries_the_building_name_for_name_matching():
    assert resolve_address([RECENTS]).name == "리센츠"


def test_sub_number_is_joined_with_hyphen():
    assert resolve_address([RECENTS_VILLE]).key == ("11710", "잠실동", "304-14")


def test_apartment_resolves_to_complex_key():
    result = resolve_address([RECENTS])
    assert result.status == "ok"
    assert result.key == ("11710", "잠실동", "22")
