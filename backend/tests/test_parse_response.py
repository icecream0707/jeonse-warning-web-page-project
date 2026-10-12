import pytest

from jeonse.parse_response import parse_response

# 실제 응답(종로구 2024-07)에서 두 행만 가져온 것.
SAMPLE = """<response>
<header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header>
<body>
<items>
<item>
<aptDong>107</aptDong>
<aptNm>인왕산아이파크</aptNm>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>143,500</dealAmount>
<jibun>60</jibun>
</item>
<item>
<aptDong> </aptDong>
<aptNm>경희궁의아침2단지</aptNm>
<cdealDay> </cdealDay>
<cdealType> </cdealType>
<dealAmount>197,000</dealAmount>
<jibun>71</jibun>
</item>
</items>
<numOfRows>10</numOfRows>
<pageNo>1</pageNo>
<totalCount>60</totalCount>
</body>
</response>"""


def test_items_and_total_count_are_read():
    items, total = parse_response(SAMPLE)
    assert total == 60
    assert len(items) == 2
    assert items[0]["aptNm"] == "인왕산아이파크"
    assert items[0]["dealAmount"] == "143,500"


def test_blank_value_becomes_empty_string():
    items, _ = parse_response(SAMPLE)
    assert items[1]["aptDong"] == ""


def test_gateway_error_message_is_surfaced():
    # 공공데이터포털 게이트웨이가 키 오류 등에서 돌려주는 형식(cmmMsgHeader).
    gateway = (
        "<OpenAPI_ServiceResponse><cmmMsgHeader><errMsg>SERVICE ERROR</errMsg>"
        "<returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg>"
        "<returnReasonCode>30</returnReasonCode></cmmMsgHeader></OpenAPI_ServiceResponse>"
    )
    with pytest.raises(ValueError, match="SERVICE_KEY_IS_NOT_REGISTERED_ERROR"):
        parse_response(gateway)


def test_error_result_code_raises():
    # 오류 응답 형식은 가정한 것: header의 resultCode가 000이 아니면 실패로 본다.
    error = "<response><header><resultCode>30</resultCode><resultMsg>SERVICE KEY IS NOT REGISTERED</resultMsg></header></response>"
    with pytest.raises(ValueError, match="SERVICE KEY"):
        parse_response(error)
