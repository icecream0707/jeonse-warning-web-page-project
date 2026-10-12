class DongRuleCheck:
    """적재 중 "동 칸이 단지명과 같으면 동 없음"이라는 규칙이 틀린 단지를 찾는다.

    같은 단지(구·읍면동·지번)에 단지명을 동으로 적은 거래와 실제 동이 섞이면 보고한다.
    """

    def __init__(self):
        self._name_as_dong = {}  # key -> 단지명
        self._real_dong = set()

    def add(self, raw):
        dong = raw["aptDong"].strip()
        if not dong:
            return
        key = (raw["sggCd"], raw["umdNm"], raw["jibun"])
        if dong == raw["aptNm"].strip():
            self._name_as_dong[key] = dong
        else:
            self._real_dong.add(key)

    def mixed(self):
        return sorted((key, name) for key, name in self._name_as_dong.items() if key in self._real_dong)
