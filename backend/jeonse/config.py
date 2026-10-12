import os
import sys
from pathlib import Path


# 실행 위치와 상관없이 backend/data/jeonse.db 를 가리킨다.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jeonse.db"

# 빌드된 React 화면(npm run build 결과). 있으면 서버가 "/"에서 같이 서빙한다.
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

# 시세 데이터를 추출한 날짜(YYYY-MM-DD). load_trades.py 를 다시 돌린 뒤 이 값을 직접 고친다.
# 결과 화면에 "시세 데이터 추출일"로 표시된다.
DATA_EXTRACTED_AT = "2026-10-12"


def read_secret(name):
    """환경변수 또는 backend/.env 에서 비밀 값을 읽는다."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if name not in os.environ and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition("=")
            if k.strip() == name:
                os.environ[name] = v.strip()
    value = os.environ.get(name)
    if not value:
        sys.exit(f"{name} 가 없습니다. backend/.env 에 넣어 주세요.")
    return value
