# 전세 위험 진단

서울 아파트의 주소·전용면적·보증금을 넣으면, 공공 실거래가로 **전세가율**(보증금 ÷ 같은 단지·면적 매매 중앙값)을
계산해 여유 있음 / 빠듯함 / 위험으로 보여 주고, 직접 확인해야 할 항목을 체크리스트로 안내합니다.
**안전 판정이 아닙니다.** 연습용 프로젝트이며 법률·금융 자문이 아닙니다.

요구사항, 결정, 한계는 [docs/PRD.md](docs/PRD.md), 용어는 [CONTEXT.md](CONTEXT.md)에 있습니다.

## 구성

- `backend/` Python(FastAPI) + SQLite. 실거래가는 미리 받아 `backend/data/jeonse.db`에 저장해 둡니다.
- `frontend/` React(Vite). 빌드하면 FastAPI가 같은 주소에서 함께 서빙합니다.

## 로컬 실행

1. `backend/.env`에 키를 넣습니다. 이 파일은 저장소에 올리지 않습니다.
   - `JUSO_KEY=` 도로명주소 검색 API 승인키
   - `DATA_GO_KR_KEY=` 공공데이터포털 국토교통부 아파트 매매 실거래가 키(데이터를 새로 받을 때만 필요)
2. 서버와 화면을 따로 띄웁니다.

```powershell
cd backend
pip install -r requirements-dev.txt
python -m uvicorn app:app --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

화면은 http://localhost:5173 입니다.

## 테스트

```powershell
cd backend
python -m pytest -q
```

## 데이터 갱신

```powershell
cd backend
python load_trades.py            # 서울 25구 × 최근 24개월 (약 600회 호출)
python load_trades.py --sgg 11710 --months 1   # 일부만 시험
```

끝나면 `backend/jeonse/config.py`의 `DATA_EXTRACTED_AT`를 그날 날짜로 고치고, 갱신한 DB를 커밋해 다시 배포합니다.
끝에 출력되는 "동 규칙 점검" 결과도 확인합니다.

## 배포 (Render 무료 웹 서비스)

설정은 [render.yaml](render.yaml)에 있습니다.

1. 이 저장소를 GitHub에 올립니다(`backend/data/jeonse.db`가 포함되어야 합니다).
2. Render에서 New → Blueprint로 저장소를 연결합니다.
3. 환경변수 `JUSO_KEY`만 Render 화면에서 직접 입력합니다. 공공데이터 키는 서버에 두지 않습니다.
4. 무료 플랜은 접속이 없으면 잠들어 첫 접속이 느릴 수 있습니다.

## 한계

근저당·선순위 보증금·세금 체납은 반영되지 않아 전세가율이 HUG 기준보다 낙관적으로 나옵니다.
서울 아파트만 지원하며 실거래가에는 신고 지연이 있습니다. 자세한 목록은 PRD의 "한계"를 보세요.
