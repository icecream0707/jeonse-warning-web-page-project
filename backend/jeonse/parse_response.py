import xml.etree.ElementTree as ET


def parse_response(xml_text):
    root = ET.fromstring(xml_text)
    if root.findtext("header/resultCode", "").strip() != "000":
        # 정상 형식(header)과 게이트웨이 오류 형식(cmmMsgHeader) 둘 다에서 진짜 메시지를 찾는다.
        message = (
            root.findtext("header/resultMsg")
            or root.findtext("cmmMsgHeader/returnAuthMsg")
            or root.findtext("cmmMsgHeader/errMsg")
            or "unknown error"
        )
        raise ValueError(message.strip())
    items = [
        {child.tag: (child.text or "").strip() for child in item}
        for item in root.findall("body/items/item")
    ]
    return items, int(root.findtext("body/totalCount", "0"))
