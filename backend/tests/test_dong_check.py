from jeonse.dong_check import DongRuleCheck


def raw(apt_dong, jibun="22", apt_nm="리센츠"):
    return {"sggCd": "11710", "umdNm": "잠실동", "jibun": jibun, "aptNm": apt_nm, "aptDong": apt_dong}


def mixed(*rows):
    check = DongRuleCheck()
    for r in rows:
        check.add(r)
    return check.mixed()


def test_name_as_dong_mixed_with_a_numeric_dong_is_reported():
    # "동 없음"으로 본 거래(동 칸에 단지명)와 실제 동이 한 단지에 같이 나오면 규칙이 틀린 것이다.
    assert mixed(raw("리센츠"), raw("201")) == [(("11710", "잠실동", "22"), "리센츠")]


def test_only_name_as_dong_is_fine():
    assert mixed(raw("현대뜨레비앙", apt_nm="현대뜨레비앙"), raw("현대뜨레비앙", apt_nm="현대뜨레비앙")) == []


def test_only_numeric_dongs_are_fine():
    assert mixed(raw("201"), raw("202")) == []


def test_blank_dong_is_ignored():
    assert mixed(raw(""), raw("리센츠")) == []
    assert mixed(raw(""), raw("201")) == []


def test_other_complexes_are_checked_separately():
    assert mixed(raw("리센츠", jibun="22"), raw("201", jibun="30", apt_nm="트리지움")) == []
