import {
    BarChart3,
    Banknote,
    CandlestickChart,
    Coins,
    CreditCard,
    Info,
    LayoutList,
    Repeat,
    Target,
    TrendingDown,
    Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { FINANCE_API, STOCK_API } from "@/lib/api-config";
import { canWiden, daysAgo, widenStart, ymd } from "./dateRange";
import { GridColumn, GridRow } from "@/components/datagrid/types";
import { FINANCE_LABELS, INFO_LABELS, RATIO_FIELDS, labelOf } from "./labels";

// ── 조회 조건 ─────────────────────────────────────────────

export type ControlKey =
    | "dateRange"
    | "period"
    | "allHistory"
    | "periodType"
    | "financeType";

export interface QueryParams {
    start: string;          // YYYYMMDD
    end: string;            // YYYYMMDD
    period: "D" | "W" | "M" | "Y";
    periodType: "A" | "Q";
    financeType: string;
    allHistory: boolean;
}

export const FINANCE_TYPES = [
    { value: "balance_sheet", label: "재무상태표" },
    { value: "income_statement", label: "손익계산서" },
    { value: "financial_ratio", label: "재무비율" },
    { value: "profit_ratio", label: "수익성비율" },
    { value: "stability_ratio", label: "안정성비율" },
    { value: "growth_ratio", label: "성장성비율" },
    { value: "other_major_ratios", label: "기타주요비율" },
];

export const PERIOD_OPTIONS = [
    { value: "D", label: "일봉" },
    { value: "W", label: "주봉" },
    { value: "M", label: "월봉" },
    { value: "Y", label: "연봉" },
];

// ── 날짜 유틸 ─────────────────────────────────────────────
// 계산은 dateRange.ts에 있다. 기존 호출부가 여기서 계속 가져다 쓰도록 다시 내보낸다.

export { canWiden, daysAgo, widenStart, ymd };

// ── 데이터셋 정의 ──────────────────────────────────────────

export interface Dataset {
    id: string;
    label: string;
    icon: LucideIcon;
    description: string;
    controls: ControlKey[];
    /** 이 데이터셋을 처음 열 때 적용할 조회 기간(일). 지정 시 기본 날짜를 덮어쓴다. */
    defaultRangeDays?: number;
    buildUrl: (iscd: string, p: QueryParams) => string;
    extract: (json: unknown, p: QueryParams) => GridRow[];
    columns: (rows: GridRow[], p: QueryParams) => GridColumn[];
    /** 조회량이 커서 시간이 걸릴 수 있는 경우 표시할 경고 */
    warning?: string;
    /**
     * 표를 쪽으로 나누지 않는다.
     * 항목·값 목록처럼 행이 수십 개뿐인 표에서는 쪽 나누기가 값을 찾는 걸 방해하기만 한다.
     */
    unpaged?: boolean;
}

const asArray = (json: unknown): GridRow[] =>
    Array.isArray(json) ? (json as GridRow[]) : [];

/** {count, data:[...]} 형태 응답에서 data만 뽑는다. */
const unwrapData = (json: unknown): GridRow[] => {
    if (Array.isArray(json)) return json as GridRow[];
    const data = (json as { data?: unknown })?.data;
    return Array.isArray(data) ? (data as GridRow[]) : [];
};

/**
 * KIS 등락 구분 코드(prdy_vrss_sign).
 * 방향은 글자 대신 화살표로 — 표에서 한 칸으로 읽히고, 옆 칸의 전일대비 부호와 어긋나지 않는다.
 */
const CHANGE_SIGN: Record<string, string> = {
    "1": "▲ 상한", "2": "▲", "3": "보합", "4": "▼ 하한", "5": "▼",
};

export const DATASETS: Dataset[] = [
    {
        id: "ohlcv",
        label: "일별 시세",
        icon: CandlestickChart,
        description: "기간별 OHLCV — DB 우선 조회, 없으면 KIS 수집 후 적재",
        controls: ["period", "dateRange", "allHistory"],
        defaultRangeDays: 365,
        buildUrl: (iscd, p) =>
            p.allHistory
                ? `${STOCK_API.OHLCV_ALL(iscd)}?start=19900101&period=${p.period}&save=true`
                : `${STOCK_API.OHLCV(iscd)}?start=${p.start}&end=${p.end}&period=${p.period}&save=true`,
        extract: asArray,
        columns: () => [
            { key: "date", label: "일자", type: "date", width: "110px" },
            { key: "open", label: "시가", type: "price" },
            { key: "high", label: "고가", type: "price" },
            { key: "low", label: "저가", type: "price" },
            { key: "close", label: "종가", type: "price" },
            { key: "change_val", label: "전일대비", type: "signed" },
            {
                key: "change_sign",
                label: "등락구분",
                width: "90px",
                format: v => CHANGE_SIGN[String(v)] ?? String(v ?? "-"),
            },
            { key: "volume", label: "거래량", type: "number" },
            { key: "amount", label: "거래대금", type: "number" },
        ],
        warning: "‘전 기간’은 상장 이후 전체를 페이지네이션으로 수집하므로 수십 초가 걸릴 수 있습니다.",
    },
    {
        id: "minute",
        label: "분봉",
        icon: BarChart3,
        description: "1분봉 — 09:00~15:30, 기간 지정 시 미보유 구간을 수집·적재",
        controls: ["dateRange"],
        defaultRangeDays: 7,
        buildUrl: (iscd, p) =>
            `${STOCK_API.MINUTE_CHART_RANGE(iscd)}?start=${p.start}&end=${p.end}`,
        extract: asArray,
        columns: () => [
            { key: "trade_date", label: "일자", type: "date", width: "110px" },
            { key: "trade_time", label: "시각", type: "time", width: "90px" },
            { key: "open_price", label: "시가", type: "price" },
            { key: "high_price", label: "고가", type: "price" },
            { key: "low_price", label: "저가", type: "price" },
            { key: "close_price", label: "종가", type: "price" },
            { key: "volume", label: "거래량", type: "number" },
            { key: "cumul_amount", label: "누적거래대금", type: "number" },
        ],
        warning: "기간이 길면 영업일마다 KIS 수집이 발생해 응답이 느려집니다. 1~2주 단위 조회를 권장합니다.",
    },
    {
        id: "investor",
        label: "투자자 수급",
        icon: Users,
        description: "개인·외국인·기관 순매수 추이",
        controls: [],
        buildUrl: iscd => `${STOCK_API.INVESTOR(iscd)}?save=true`,
        extract: asArray,
        columns: () => [
            { key: "date", label: "일자", type: "date", width: "110px" },
            { key: "individual_net", label: "개인 순매수", type: "signed" },
            { key: "foreign_net", label: "외국인 순매수", type: "signed" },
            { key: "institution_net", label: "기관 순매수", type: "signed" },
        ],
    },
    {
        id: "orderbook",
        label: "호가",
        icon: LayoutList,
        description: "실시간 10단계 호가 — 매도(파랑)는 위, 매수(빨강)는 아래",
        controls: [],
        buildUrl: iscd => STOCK_API.ORDERBOOK(iscd),
        extract: json => {
            const ob = json as {
                ask_prices?: number[]; bid_prices?: number[];
                ask_quantities?: number[]; bid_quantities?: number[];
            } | null;
            if (!ob?.ask_prices) return [];
            const depth = Math.max(ob.ask_prices.length, ob.bid_prices?.length ?? 0);
            return Array.from({ length: depth }, (_, i) => ({
                step: `${i + 1}호가`,
                ask_qty: ob.ask_quantities?.[i] ?? null,
                ask_price: ob.ask_prices?.[i] ?? null,
                bid_price: ob.bid_prices?.[i] ?? null,
                bid_qty: ob.bid_quantities?.[i] ?? null,
            }));
        },
        columns: () => [
            { key: "step", label: "단계", width: "80px" },
            { key: "ask_qty", label: "매도잔량", type: "number" },
            { key: "ask_price", label: "매도호가", type: "price" },
            { key: "bid_price", label: "매수호가", type: "price" },
            { key: "bid_qty", label: "매수잔량", type: "number" },
        ],
    },
    {
        id: "short-sell",
        label: "공매도",
        icon: TrendingDown,
        description: "일자별 공매도 거래량·거래대금 (실전투자 계정 필요)",
        controls: ["dateRange"],
        defaultRangeDays: 90,
        buildUrl: (iscd, p) =>
            `${STOCK_API.SHORT_SELL(iscd)}?start=${p.start}&end=${p.end}&save=true`,
        extract: unwrapData,
        columns: () => [
            { key: "stck_bsop_date", label: "일자", type: "date", width: "110px" },
            { key: "stck_clpr", label: "종가", type: "price" },
            { key: "prdy_ctrt", label: "전일대비율", type: "percent" },
            { key: "ssts_cntg_qty", label: "공매도 수량", type: "number" },
            { key: "ssts_vol_rlim", label: "거래량 비중", type: "percent" },
            { key: "ssts_tr_pbmn", label: "공매도 대금", type: "number" },
            { key: "avrg_prc", label: "공매도 평균가", type: "price" },
            { key: "acml_ssts_cntg_qty", label: "누적 공매도", type: "number" },
            { key: "acml_vol", label: "거래량", type: "number" },
        ],
    },
    {
        id: "credit",
        label: "신용잔고",
        icon: CreditCard,
        description: "일자별 신용융자 잔고 수량·금액·비율 (실전투자 계정 필요)",
        controls: ["dateRange"],
        defaultRangeDays: 90,
        buildUrl: (iscd, p) =>
            `${STOCK_API.CREDIT(iscd)}?start=${p.start}&end=${p.end}&save=true`,
        extract: unwrapData,
        columns: () => [
            { key: "deal_date", label: "일자", type: "date", width: "110px" },
            { key: "stck_prpr", label: "종가", type: "price" },
            { key: "prdy_ctrt", label: "전일대비율", type: "percent" },
            { key: "whol_loan_rmnd_stcn", label: "융자잔고 주수", type: "number" },
            { key: "whol_loan_rmnd_amt", label: "융자잔고 금액", type: "number" },
            { key: "whol_loan_rmnd_rate", label: "융자잔고 비율", type: "percent" },
            { key: "whol_loan_new_stcn", label: "융자 신규", type: "number" },
            { key: "whol_loan_rdmp_stcn", label: "융자 상환", type: "number" },
            { key: "whol_stln_rmnd_stcn", label: "대주잔고 주수", type: "number" },
        ],
    },
    {
        id: "loan-trans",
        label: "대차거래",
        icon: Repeat,
        description: "대차잔고·신규·상환 추이 — 잔고가 늘면 공매도 압력이 쌓인다 (실전투자 계정 필요)",
        controls: ["dateRange"],
        defaultRangeDays: 90,
        buildUrl: (iscd, p) =>
            `${STOCK_API.LOAN_TRANS(iscd)}?start=${p.start}&end=${p.end}&save=true`,
        extract: unwrapData,
        columns: () => [
            { key: "bsop_date", label: "일자", type: "date", width: "110px" },
            { key: "stck_prpr", label: "종가", type: "price" },
            { key: "prdy_ctrt", label: "전일대비율", type: "percent" },
            { key: "rmnd_stcn", label: "대차잔고 주수", type: "number" },
            { key: "prdy_rmnd_vrss", label: "잔고 증감", type: "signed" },
            { key: "rmnd_amt", label: "대차잔고 금액", type: "number" },
            { key: "new_stcn", label: "신규 체결", type: "number" },
            { key: "rdmp_stcn", label: "상환", type: "number" },
            { key: "acml_vol", label: "거래량", type: "number" },
        ],
    },
    {
        id: "finance",
        label: "재무제표",
        icon: Banknote,
        description: "재무상태표·손익계산서·각종 비율 (단위: 억원 / %)",
        controls: ["financeType", "periodType"],
        buildUrl: (iscd, p) =>
            `${FINANCE_API.STATEMENT(iscd, p.financeType)}?period_type=${p.periodType}&save=true`,
        // FinancePeriodRow[] → period + data 스프레드로 평탄화
        extract: json =>
            asArray(json).map(row => {
                const data = (row.data ?? {}) as Record<string, unknown>;
                return { period: row.period, ...data };
            }),
        columns: rows => {
            const keys: string[] = [];
            rows.forEach(row => {
                Object.keys(row).forEach(k => {
                    if (k !== "period" && k !== "stac_yymm" && !keys.includes(k)) keys.push(k);
                });
            });
            return [
                { key: "period", label: "결산년월", type: "date", width: "110px" },
                ...keys.map<GridColumn>(k => ({
                    key: k,
                    label: labelOf(FINANCE_LABELS, k),
                    type: RATIO_FIELDS.has(k) ? "percent" : "number",
                })),
            ];
        },
    },
    {
        id: "dividend",
        label: "배당",
        icon: Coins,
        description: "배당기준일·주당배당금·지급일",
        controls: ["dateRange"],
        defaultRangeDays: 1095,
        buildUrl: (iscd, p) =>
            `${FINANCE_API.DIVIDEND(iscd)}?start=${p.start}&end=${p.end}&save=true`,
        extract: asArray,
        columns: () => [
            { key: "record_date", label: "배당기준일", type: "date", width: "120px" },
            { key: "dividend_type", label: "배당구분", width: "110px" },
            { key: "amount_per_share", label: "주당배당금", type: "price" },
            { key: "pay_date", label: "지급일", type: "date", width: "120px" },
        ],
    },
    {
        id: "estimate",
        label: "추정실적",
        icon: Target,
        description: "확정 실적 + 증권사 컨센서스 (금액 단위: 억원, E 표시가 추정치)",
        controls: [],
        buildUrl: iscd => `${FINANCE_API.ESTIMATE(iscd)}?save=true`,
        extract: asArray,
        columns: () => [
            {
                key: "period_label",
                label: "기간",
                width: "110px",
                format: (v, row) => `${v ?? "-"}${row.is_estimate ? " (추정)" : ""}`,
            },
            { key: "revenue", label: "매출액", type: "number" },
            { key: "revenue_growth", label: "매출 증감률", type: "percent" },
            { key: "operating_profit", label: "영업이익", type: "number" },
            { key: "op_growth", label: "영업이익 증감률", type: "percent" },
            { key: "net_income", label: "당기순이익", type: "number" },
            { key: "net_growth", label: "순이익 증감률", type: "percent" },
            { key: "ebitda", label: "EBITDA", type: "number" },
            { key: "eps", label: "EPS(원)", type: "number" },
            { key: "per", label: "PER", type: "number" },
            { key: "pbr", label: "PBR", type: "number" },
            { key: "roe", label: "ROE", type: "percent" },
            { key: "debt_ratio", label: "부채비율", type: "percent" },
            { key: "opinion", label: "투자의견", width: "90px" },
        ],
    },
    {
        id: "info",
        label: "종목 기본정보",
        icon: Info,
        description: "상장일·상장주수·액면가·업종 등 KIS 원본 필드 전체",
        controls: [],
        // 한 종목의 속성 목록이라 시계열이 아니다 — 쪽을 넘겨 가며 찾을 표가 아니다
        unpaged: true,
        buildUrl: iscd => `${FINANCE_API.INFO_BASIC(iscd)}?save=true`,
        extract: json => {
            if (!json || typeof json !== "object" || Array.isArray(json)) return [];
            return Object.entries(json as Record<string, unknown>)
                .filter(([, v]) => v !== null && v !== undefined && String(v).trim() !== "")
                .map(([key, value]) => ({
                    label: labelOf(INFO_LABELS, key),
                    field: key,
                    value: String(value).trim(),
                }));
        },
        columns: () => [
            { key: "label", label: "항목", width: "220px" },
            { key: "value", label: "값" },
            { key: "field", label: "원본 필드", width: "200px" },
        ],
    },
];

export const DEFAULT_PARAMS: QueryParams = {
    start: daysAgo(365),
    end: ymd(new Date()),
    period: "D",
    periodType: "A",
    financeType: "balance_sheet",
    allHistory: false,
};
