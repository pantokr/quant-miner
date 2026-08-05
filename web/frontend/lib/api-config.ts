// 모든 API 호출은 /api/proxy를 통해 라우팅됩니다.
// - 로컬: next.config.ts 리라이트 → http://127.0.0.1:8000
// - Vercel: vercel.json 리라이트 → http://168.107.24.190:8000
//
// 직접 IP를 사용하면 Vercel(HTTPS)에서 mixed content 오류 발생하므로
// 절대 http://로 시작하는 URL을 여기에 넣지 마세요.
const PROXY = "/api/proxy";

export const STOCK_API = {
    MINUTE_CHART: (iscd: string) => `${PROXY}/stock/${iscd}/minute-chart`,
    MINUTE_CHART_RANGE: (iscd: string) => `${PROXY}/stock/${iscd}/minute-chart/range`,
    OHLCV: (iscd: string) => `${PROXY}/stock/${iscd}/ohlcv`,
    OHLCV_ALL: (iscd: string) => `${PROXY}/stock/${iscd}/ohlcv/all`,
    CURRENT: (iscd: string) => `${PROXY}/stock/${iscd}/current`,
    ORDERBOOK: (iscd: string) => `${PROXY}/stock/${iscd}/orderbook`,
    INVESTOR: (iscd: string) => `${PROXY}/stock/${iscd}/investor`,
    SHORT_SELL: (iscd: string) => `${PROXY}/stock/${iscd}/short-sell`,
    CREDIT: (iscd: string) => `${PROXY}/stock/${iscd}/credit`,
    LOAN_TRANS: (iscd: string) => `${PROXY}/stock/${iscd}/loan-trans`,
};

export const MASTER_API = {
    SEARCH: `${PROXY}/stock/search`,
    ONE: (iscd: string) => `${PROXY}/stock/master/${iscd}`,
};

export const FINANCE_API = {
    // finance_type: balance_sheet | income_statement | financial_ratio |
    //               profit_ratio | stability_ratio | growth_ratio
    STATEMENT: (iscd: string, financeType: string) => `${PROXY}/finance/${iscd}/${financeType}`,
    INFO_BASIC: (iscd: string) => `${PROXY}/finance/${iscd}/info/basic`,
    DIVIDEND: (iscd: string) => `${PROXY}/finance/${iscd}/dividend`,
    ESTIMATE: (iscd: string) => `${PROXY}/finance/${iscd}/estimate`,
};

export const ACCOUNT_API = {
    BALANCE: `${PROXY}/account/balance`,
    DAILY_CCLD: `${PROXY}/account/daily-ccld`,
};

export const RANKING_API = {
    FLUCTUATION: `${PROXY}/ranking/fluctuation`,
    VOLUME: `${PROXY}/ranking/volume`,
    FOREIGN: `${PROXY}/ranking/foreign`,
    INSTITUTION: `${PROXY}/ranking/institution`,
};

export const ML_API = {
    FEATURES: `${PROXY}/ml/features`,
    MODELS: `${PROXY}/ml/models`,
    TRAIN: `${PROXY}/ml/train`,
    JOB: (id: string) => `${PROXY}/ml/jobs/${id}`,
};
