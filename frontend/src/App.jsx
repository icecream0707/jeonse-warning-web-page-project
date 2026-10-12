import { useState } from "react";

const MESSAGES = {
  not_found: "검색 결과가 없습니다. 도로명주소(예: 올림픽로 135)로 다시 검색해 보세요.",
  not_apartment: "공동주택(아파트)이 아닙니다. 이 서비스는 서울 아파트만 지원합니다.",
  not_seoul: "서울이 아닙니다. 이 서비스는 서울 아파트만 지원합니다.",
  mountain: "산 번지 주소는 지원하지 않습니다.",
  no_data: "검색된 아파트 중 실거래가 데이터가 있는 단지가 없습니다. 도로명주소로 다시 검색해 보세요.",
};

const BASIS = {
  dong_12m: "선택한 동 · 최근 12개월",
  complex_12m: "단지 전체 · 최근 12개월",
  complex_24m: "단지 전체 · 최근 24개월 (거래가 적어 기간을 넓혔습니다)",
};

const LEVEL_COLOR = { "여유 있음": "#2e9e5b", 빠듯함: "#e0a800", 위험: "#d64545" };

const CHECKLIST = [
  "등기부등본에서 근저당·압류·가처분 확인. 근저당 + 보증금이 시세의 80% 이내인지 계산",
  "선순위 보증금(다른 세입자) 규모 확인 (HUG는 선순위채권이 주택가격 60% 초과 시 가입 제한)",
  "집주인 본인 확인과 계약 당사자 일치",
  "국세·지방세 체납 여부(납세증명서)",
  "인근 시세 직접 확인",
  "HUG 전세보증보험 가입 가능 여부 조회 (보증금 상한: 수도권 7억 원)",
  "건축물대장에서 위반건축물 표시 확인 (정부24 또는 세움터 열람)",
];

const won = (man) => {
  const eok = Math.floor(man / 10000);
  const rest = Math.round(man % 10000);
  return `${eok ? eok + "억 " : ""}${rest ? rest.toLocaleString() + "만원" : eok ? "" : "0원"}`.trim();
};

async function getJson(url, init) {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `오류 ${res.status}`);
  return res.json();
}

export default function App() {
  const [q, setQ] = useState("");
  const [addr, setAddr] = useState(null); // { name, key }
  const [candidates, setCandidates] = useState([]);
  const [options, setOptions] = useState(null);
  const [area, setArea] = useState("");
  const [dong, setDong] = useState("");
  const [deposit, setDeposit] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const fail = (e) => setError(e.message || String(e));

  const pick = async (key, name) => {
    setAddr({ key, name });
    setCandidates([]);
    setResult(null);
    setDong("");
    const o = await getJson(`/api/options?${new URLSearchParams({ sgg: key[0], umd: key[1], jibun: key[2] })}`);
    setOptions(o);
    setArea(o.areas.length ? String(o.areas[0][0]) : "");
  };

  const search = async (e) => {
    e.preventDefault();
    setError(""); setAddr(null); setOptions(null); setResult(null); setCandidates([]);
    try {
      const r = await getJson(`/api/address?${new URLSearchParams({ q })}`);
      if (r.status === "ok") await pick(r.key, q);
      else if (r.status === "choose") setCandidates(r.candidates);
      else setError(MESSAGES[r.status] || r.status);
    } catch (err) { fail(err); }
  };

  const run = async (e) => {
    e.preventDefault();
    setError(""); setResult(null);
    try {
      const sent = { area: Number(area), dong: dong || null, deposit: Number(deposit) };
      const r = await getJson("/api/diagnose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sgg: addr.key[0], umd: addr.key[1], jibun: addr.key[2], ...sent }),
      });
      // 결과와 함께 진단에 쓴 값을 저장해, 이후 입력을 바꿔도 카드가 어긋나지 않게 한다.
      setResult({ ...r, sent });
    } catch (err) { fail(err); }
  };

  return (
    <main>
      <h1>전세 위험 진단</h1>
      <p className="lead">서울 아파트 주소와 보증금을 넣으면 공공 실거래가로 확인되는 신호를 보여 드립니다. 안전 판정이 아닙니다.</p>

      <form onSubmit={search} className="row">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="도로명주소 (예: 올림픽로 135)" minLength={2} required />
        <button>검색</button>
      </form>

      {error && <p className="error">{error}</p>}

      {candidates.length > 0 && (
        <div className="card">
          <p>여러 건이 검색되었습니다. 계약할 아파트를 골라 주세요.</p>
          {candidates.map(([name, key]) => (
            <button key={key.join()} className="link" onClick={() => pick(key, name).catch(fail)}>
              {name} ({key[1]} {key[2]})
            </button>
          ))}
        </div>
      )}

      {addr && options && (
        <form onSubmit={run} className="card">
          <p><b>{addr.name}</b> ({addr.key[1]} {addr.key[2]})</p>
          {options.areas.length === 0 ? (
            <p className="error">이 단지의 거래 데이터가 없습니다.</p>
          ) : (
            <>
              <label>전용면적
                <select value={area} onChange={(e) => setArea(e.target.value)}>
                  {options.areas.map(([a, n]) => <option key={a} value={a}>{a}㎡ (거래 {n}건)</option>)}
                </select>
              </label>
              {options.dongs.length > 0 && (
                <label>동
                  <select value={dong} onChange={(e) => setDong(e.target.value)}>
                    <option value="">모름</option>
                    {options.dongs.map((d) => <option key={d} value={d}>{d}동</option>)}
                  </select>
                </label>
              )}
              <label>보증금 (만원)
                <input type="number" min="1" value={deposit} onChange={(e) => setDeposit(e.target.value)} required />
                {deposit > 0 && <small>{won(Number(deposit))}</small>}
              </label>
              <button>진단</button>
            </>
          )}
        </form>
      )}

      {result && <Result r={result} />}

      <Checklist highlightPrice={result?.status === "insufficient"} />
      <p className="disclaimer">
        이 서비스는 연습용이며 법률·금융 자문이 아닙니다. 근저당·선순위 보증금·세금 체납은 반영되지 않아 실제 위험은 더 높을 수 있고,
        실거래가에는 신고 지연이 있습니다. 구간 기준(70%, 80%)은 HUG 공개 안내를 참고한 임시값이며 공식 기준이 아닙니다.
      </p>
    </main>
  );
}

function Result({ r }) {
  const { deposit, dong: dongChosen } = r.sent;
  if (r.status === "insufficient") {
    return (
      <div className="card">
        <h2>거래 부족</h2>
        <p>같은 단지·면적의 최근 24개월 매매가 {r.count}건뿐이라 전세가율을 계산하지 않았습니다. 인근 시세를 직접 확인하세요.</p>
        <p className="note">시세 데이터 추출일: {r.data_extracted_at}</p>
      </div>
    );
  }
  const pct = r.ratio * 100;
  const color = LEVEL_COLOR[r.level];
  return (
    <div className="card">
      <h2>전세가율 <span style={{ color }}>{pct.toFixed(1)}% · {r.level}</span></h2>
      <div className="bar" role="img" aria-label={`전세가율 ${pct.toFixed(1)}%`}>
        <i style={{ width: "70%", background: LEVEL_COLOR["여유 있음"] }} />
        <i style={{ width: "10%", background: LEVEL_COLOR["빠듯함"] }} />
        <i style={{ width: "20%", background: LEVEL_COLOR["위험"] }} />
        <span className="marker" style={{ left: `${Math.min(pct, 100)}%` }} />
        {[70, 80, 90].map((t) => <span key={t} className="tick" style={{ left: `${t}%` }}>{t}%</span>)}
      </div>
      <p className="note">90%는 HUG 보증 가입 심사선(선순위채권 포함 기준) 참고선입니다. 우리 값은 선순위채권을 반영하지 않습니다.</p>
      <p>보증금 {won(deposit)} ÷ 매매 중앙값 {won(r.median)}</p>
      <p>매매 {r.count}건 · 최저 {won(r.min)} · 최고 {won(r.max)}</p>
      <p className="note">기준: {BASIS[r.basis]}</p>
      <p className="note">시세 데이터 추출일: {r.data_extracted_at}</p>
      {dongChosen && !r.basis.startsWith("dong") && (
        <p className="note">선택한 동의 거래가 적어 단지 전체로 계산했습니다.</p>
      )}
      {r.dong_medians?.length > 0 && (
        <details open>
          <summary>동별 최근 12개월 중앙값 (같은 면적)</summary>
          <table>
            <tbody>
              {r.dong_medians.map(([d, n, m]) => (
                <tr key={d}><td>{d}동</td><td>{won(m)}</td><td>{n}건{n < 3 ? " (적음)" : ""}</td></tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </div>
  );
}

function Checklist({ highlightPrice }) {
  return (
    <section className="card">
      <h2>직접 확인해야 할 항목</h2>
      <ol>
        {CHECKLIST.map((t, i) => (
          <li key={i} className={highlightPrice && i === 4 ? "hot" : ""}>{t}</li>
        ))}
      </ol>
    </section>
  );
}
