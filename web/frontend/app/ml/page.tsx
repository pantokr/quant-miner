"use client";

import { useEffect, useState } from "react";
import { ML_API } from "@/lib/api-config";

type Result = {
  spec: Record<string, unknown>;
  samples: { total: number; train: number; test: number };
  metrics: Record<string, number>;
  feature_importance: { feature: string; importance: number }[];
};

const box: React.CSSProperties = {
  border: "1px solid #ddd", borderRadius: 8, padding: 16, marginBottom: 16,
};

export default function MlPage() {
  const [features, setFeatures] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [models, setModels] = useState<Record<string, string[]>>({});
  const [iscd, setIscd] = useState("005930");
  const [target, setTarget] = useState<"return" | "direction">("return");
  const [model, setModel] = useState("ridge");
  const [horizon, setHorizon] = useState(5);
  const [limit, setLimit] = useState(0);
  const [status, setStatus] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch(ML_API.FEATURES).then((r) => r.json()).then((d) => {
      setFeatures(d.features);
      setSelected(d.default);
    }).catch(() => setError("특징 목록 로드 실패 (백엔드 확인)"));
    fetch(ML_API.MODELS).then((r) => r.json()).then(setModels).catch(() => {});
  }, []);

  const modelOpts = models[target] || [];
  useEffect(() => {
    if (modelOpts.length && !modelOpts.includes(model)) setModel(modelOpts[0]);
  }, [target, models]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (f: string) =>
    setSelected((s) => (s.includes(f) ? s.filter((x) => x !== f) : [...s, f]));

  const submit = async () => {
    setBusy(true); setError(""); setResult(null); setStatus("제출 중...");
    try {
      const res = await fetch(ML_API.TRAIN, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ iscd, features: selected, target, model, horizon, limit }),
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error(e.detail || "제출 실패");
      }
      const { job_id } = await res.json();
      setStatus("학습 중...");
      for (let i = 0; i < 120; i++) {
        await new Promise((r) => setTimeout(r, 1500));
        const j = await (await fetch(ML_API.JOB(job_id))).json();
        setStatus(j.status);
        if (j.status === "done") { setResult(j.result); break; }
        if (j.status === "error") { setError(j.error || "학습 오류"); break; }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ maxWidth: 820, margin: "24px auto", padding: "0 16px", fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 16 }}>가격 예측 모델 학습</h1>

      <div style={box}>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 12 }}>
          <label>종목코드{" "}
            <input value={iscd} onChange={(e) => setIscd(e.target.value)} style={{ width: 90 }} />
          </label>
          <label>타깃{" "}
            <select value={target} onChange={(e) => setTarget(e.target.value as "return" | "direction")}>
              <option value="return">수익률(회귀)</option>
              <option value="direction">방향(분류)</option>
            </select>
          </label>
          <label>모델{" "}
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              {modelOpts.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </label>
          <label>지평(분){" "}
            <input type="number" value={horizon} onChange={(e) => setHorizon(+e.target.value)} style={{ width: 60 }} />
          </label>
          <label>표본제한{" "}
            <input type="number" value={limit} onChange={(e) => setLimit(+e.target.value)} style={{ width: 90 }} title="0=전체, 최근 N봉" />
          </label>
        </div>

        <div style={{ marginBottom: 8, fontWeight: 600 }}>특징 선택 ({selected.length}개)</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 14px" }}>
          {features.map((f) => (
            <label key={f} style={{ fontSize: 13 }}>
              <input type="checkbox" checked={selected.includes(f)} onChange={() => toggle(f)} /> {f}
            </label>
          ))}
        </div>

        <button onClick={submit} disabled={busy || selected.length === 0}
          style={{ marginTop: 14, padding: "8px 18px", cursor: busy ? "wait" : "pointer" }}>
          {busy ? "학습 중..." : "학습 실행"}
        </button>
        {status && <span style={{ marginLeft: 12, color: "#666" }}>상태: {status}</span>}
      </div>

      {error && <div style={{ ...box, borderColor: "#e33", color: "#c00" }}>오류: {error}</div>}

      {result && (
        <div style={box}>
          <div style={{ color: "#666", marginBottom: 8 }}>
            표본 {result.samples.total.toLocaleString()} (train {result.samples.train.toLocaleString()} / test {result.samples.test.toLocaleString()})
          </div>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>메트릭</div>
          <table style={{ borderCollapse: "collapse", marginBottom: 14 }}>
            <tbody>
              {Object.entries(result.metrics).map(([k, v]) => (
                <tr key={k}>
                  <td style={{ padding: "2px 16px 2px 0", color: "#444" }}>{k}</td>
                  <td style={{ padding: "2px 0", fontWeight: 600, textAlign: "right" }}>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>특징 중요도</div>
          {result.feature_importance.map((row) => (
            <div key={row.feature} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
              <span style={{ width: 90, fontSize: 13 }}>{row.feature}</span>
              <span style={{
                display: "inline-block", height: 12,
                width: `${Math.max(2, row.importance * 240)}px`, background: "#4a90d9",
              }} />
              <span style={{ fontSize: 12, color: "#666" }}>{row.importance}</span>
            </div>
          ))}
        </div>
      )}

      <p style={{ color: "#999", fontSize: 12 }}>
        Dir.Acc가 50%(회귀)·majority_baseline(분류)를 유의미하게 넘어야 예측력이 있는 것. 단기 분봉은 대개 그 부근.
      </p>
    </div>
  );
}
