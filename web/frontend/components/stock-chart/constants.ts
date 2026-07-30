export type ChartPeriod = "minute" | "daily" | "monthly" | "yearly";
export type OhlcvPeriod = Exclude<ChartPeriod, "minute">;

export const PERIOD_LABELS: Record<ChartPeriod, string> = {
    minute: "분봉",
    daily: "일봉",
    monthly: "월봉",
    yearly: "연봉",
};

// 기간별 고정 표시 너비 (일봉 60일, 월봉 36개월, 연봉 15년)
export const FIXED_WINDOW: Record<OhlcvPeriod, number> = { daily: 60, monthly: 36, yearly: 15 };

// ← 이전 / 이후 → 버튼 한 번 클릭 시 이동량
export const PAN_STEP: Record<OhlcvPeriod, number> = { daily: 10, monthly: 3, yearly: 1 };

// X축에 표시할 최대 tick 수 (시작·끝 포함, 겹침 방지)
export const MAX_TICKS: Record<OhlcvPeriod, number> = { daily: 3, monthly: 3, yearly: 3 };

export const GRAD_ID: Record<OhlcvPeriod, string> = {
    daily: "colorPriceDaily",
    monthly: "colorPriceMonthly",
    yearly: "colorPriceYearly",
};

/** 축 라벨이 잘리지 않도록 사방 여백 (특히 아래·오른쪽) */
export const CHART_MARGIN = { top: 10, right: 24, left: 8, bottom: 8 };

/**
 * 가격 축 눈금 축약 — 소수점을 버리고 자연수로만 표시해 라벨 길이를 최소화한다.
 * 예) 13,726,154,839,133 → "14조",  208,500 → "209천"
 */
export function compactPrice(v: number): string {
    const abs = Math.abs(v);
    if (abs >= 1e12) return `${Math.round(v / 1e12)}조`;
    if (abs >= 1e8) return `${Math.round(v / 1e8)}억`;
    if (abs >= 1e4) return `${Math.round(v / 1e4)}만`;
    return String(Math.round(v));
}

/** 눈금 글자 스타일. Y축은 width="auto"가 이 크기를 재서 축 폭을 잡는다. */
export const AXIS_TICK = { fill: "#94a3b8", fontSize: 10, fontWeight: 700 } as const;

export type ChartStyle = "line" | "candle";

export const STYLE_LABELS: Record<ChartStyle, string> = {
    line: "선",
    candle: "캔들",
};

export const TOOLTIP_STYLE = {
    borderRadius: "12px",
    border: "none",
    boxShadow: "0 10px 15px -3px rgba(0,0,0,0.1)",
    backgroundColor: "var(--chakra-colors-bg-panel)",
};
