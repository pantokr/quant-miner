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

/**
 * 차트·호가·투자자 탭이 공유하는 본문 높이.
 *
 * 탭마다 내용 높이가 다르면 탭을 옮길 때마다 카드가 늘었다 줄었다 해서 오른쪽 패널이
 * 출렁인다. 세 탭 모두 이 높이에 맞춰 내용을 채우거나 줄인다.
 */
export const TAB_BODY_PX = 360;
export const TAB_BODY_H = `${TAB_BODY_PX}px`;

/** 축 라벨이 잘리지 않도록 사방 여백 (특히 아래·오른쪽) */
export const CHART_MARGIN = { top: 10, right: 24, left: 12, bottom: 8 };

/** Y축 라벨과 그래프 사이 간격. width="auto"가 잰 글자 폭에 이만큼이 더 붙는다. */
export const Y_TICK_MARGIN = 10;

/**
 * 가격 축 눈금 표기.
 *
 * 예전에는 1만 이상을 전부 "N만"으로 반올림했는데, 주가는 눈금 간격이 1~2%라
 * 89,000 / 90,500 / 92,000 / 93,500이 모두 "9만"으로 뭉개져 축이 무의미해졌다.
 * 그래서 원 단위 구간은 축약하지 않고 자릿수 구분만 넣는다 — 눈금이 절대 겹치지 않는다.
 * 폭은 YAxis width="auto"가 실제 글자를 재서 잡으므로 길어져도 잘리지 않는다.
 *
 * 억/조 단위(시가총액·거래대금)는 자릿수가 너무 길어 축약하되, 100단위 미만이면
 * 소수 한 자리를 남겨 인접 눈금이 같은 값으로 반올림되지 않게 한다.
 * 예) 1,234,500 → "1,234,500",  350,000,000 → "3.5억",  13,726,154,839,133 → "13.7조"
 */
export function compactPrice(v: number): string {
    const abs = Math.abs(v);
    if (abs >= 1e12) return `${scaled(v, 1e12)}조`;
    if (abs >= 1e8) return `${scaled(v, 1e8)}억`;
    return Math.round(v).toLocaleString();
}

/** 100단위 미만이면 소수 한 자리를 남긴다 (인접 눈금이 같은 값으로 뭉치는 것 방지) */
function scaled(v: number, unit: number): string {
    const n = v / unit;
    return Math.abs(n) < 100 ? n.toFixed(1) : String(Math.round(n));
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
