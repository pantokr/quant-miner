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

export const TOOLTIP_STYLE = {
    borderRadius: "12px",
    border: "none",
    boxShadow: "0 10px 15px -3px rgba(0,0,0,0.1)",
    backgroundColor: "var(--chakra-colors-bg-panel)",
};
