/**
 * Y축 도메인·눈금 계산.
 *
 * 예전에는 recharts 기본 도메인([0, auto])에 값 단위 축약을 얹었다. 둘이 겹쳐 축이
 * 사실상 읽히지 않았다 —
 *   1) 208,500~265,000짜리 주가가 0부터 그려져 선이 위쪽에 눌린 채 평평해 보였고,
 *   2) 축약이 자연수로 반올림해 208,500과 214,000이 똑같이 "21만"으로 찍혔다.
 *
 * 그래서 눈금을 직접 잡는다. 1·2·2.5·5 배수 계단으로 도메인을 자르면 눈금 간격이
 * 라벨의 유효 자릿수를 정해 주므로 인접 눈금이 같은 글자로 뭉칠 수 없다.
 * (stock-chart의 compactPrice가 값 하나만 보고 푸는 문제를 축 전체로 넓힌 것)
 */
import { TableRow, toNumber } from "./parseTable";

export interface AxisScale {
    domain: [number, number];
    ticks: number[];
    format: (v: number) => string;
}

/** 사람이 암산으로 나누는 눈금 간격만 쓴다 */
const NICE_STEPS = [1, 2, 2.5, 5, 10];

/** 눈금이 아무리 늘어도 이 개수를 넘기지 않는다 (라벨끼리 겹친다) */
const MAX_TICKS = 12;

function niceStep(rough: number): number {
    if (!(rough > 0)) return 1;
    const magnitude = 10 ** Math.floor(Math.log10(rough));
    const normalized = rough / magnitude;
    return (NICE_STEPS.find(s => normalized <= s * 1.000001) ?? 10) * magnitude;
}

/**
 * 눈금 간격을 오차 없이 적기 위해 필요한 소수 자리.
 * 간격 자체를 보고 정해야 한다 — 2.5 계단을 정수로 적으면 2.5와 5가 "3"과 "5"로 어긋난다.
 */
function decimalsFor(step: number): number {
    for (let d = 0; d <= 8; d++) {
        const scaled = step * 10 ** d;
        if (Math.abs(scaled - Math.round(scaled)) < 1e-9 * Math.max(1, Math.abs(scaled))) return d;
    }
    return 8;
}

function withDecimals(n: number, step: number): string {
    const digits = decimalsFor(step);
    return n.toLocaleString("ko-KR", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
    });
}

/**
 * 억/조만 축약하고 원 단위는 자릿수 구분만 넣는다 — 앱의 다른 차트와 같은 표기.
 * 소수 자리는 눈금 간격이 정하므로 인접 눈금이 같은 값으로 반올림되지 않는다.
 * 예) 간격 2만 → "220,000",  간격 5천억 → "13.5조"
 */
function buildFormat(step: number): (v: number) => string {
    return (v: number) => {
        const abs = Math.abs(v);
        if (abs >= 1e12) return `${withDecimals(v / 1e12, step / 1e12)}조`;
        if (abs >= 1e8) return `${withDecimals(v / 1e8, step / 1e8)}억`;
        return withDecimals(v, step);
    };
}

/**
 * 값들이 실제로 놓인 구간에 맞춰 축을 잡는다.
 *
 * includeZero: 막대는 길이가 곧 크기라 0을 잘라 내면 거짓말이 된다. 선·영역·산점도는
 * 반대로 0에 묶어 두면 변화 폭이 뭉개지므로 데이터 구간만 본다.
 */
export function buildYScale(
    values: number[],
    { includeZero, targetTicks = 5 }: { includeZero: boolean; targetTicks?: number },
): AxisScale | null {
    let min = Infinity;
    let max = -Infinity;
    for (const v of values) {
        if (!Number.isFinite(v)) continue;
        if (v < min) min = v;
        if (v > max) max = v;
    }
    if (min === Infinity) return null;

    if (includeZero) {
        min = Math.min(0, min);
        max = Math.max(0, max);
    }

    if (min === max) {
        // 값이 하나뿐이거나 전부 같다 — 그 값을 가운데 두고 축을 편다
        const spread = Math.abs(min) * 0.02 || 1;
        min -= spread;
        max += spread;
    } else if (!includeZero) {
        // 첫·끝 점이 축 끝에 딱 붙지 않도록 조금 띄운다
        const pad = (max - min) * 0.04;
        min -= pad;
        max += pad;
    }

    const step = niceStep((max - min) / Math.max(1, targetTicks - 1));
    const lo = Math.floor(min / step) * step;
    const hi = Math.ceil(max / step) * step;

    const count = Math.min(MAX_TICKS, Math.round((hi - lo) / step) + 1);
    // 부동소수 누적 오차가 라벨에 새지 않도록 자른다 (0.1 간격의 0.30000000000000004 방지)
    const ticks = Array.from({ length: count }, (_, i) => Number((lo + i * step).toFixed(12)));

    return { domain: [lo, hi], ticks, format: buildFormat(step) };
}

/** 한 열의 유한한 숫자 값만 뽑는다 */
function columnValues(rows: TableRow[], key: string): number[] {
    const out: number[] = [];
    for (const r of rows) {
        const n = toNumber(r[key]);
        if (n !== null) out.push(n);
    }
    return out;
}

/**
 * 선택한 열들의 크기 차이 배수 (가장 큰 열 / 가장 작은 열).
 *
 * 종가(20만)와 거래량(6천만)처럼 자릿수가 다른 열을 한 축에 겹치면 작은 쪽이 바닥에
 * 눌려 선이 되어 버린다. 축을 둘로 나누는 건 없는 상관관계를 지어내므로 하지 않고,
 * 대신 이 배수가 크면 지수 비교를 권한다.
 */
export function magnitudeGap(rows: TableRow[], keys: string[]): number {
    if (keys.length < 2) return 1;
    const peaks = keys
        .map(k => Math.max(0, ...columnValues(rows, k).map(Math.abs)))
        .filter(v => v > 0);
    if (peaks.length < 2) return 1;
    return Math.max(...peaks) / Math.min(...peaks);
}

/**
 * 지수 비교(첫 값 = 100)를 쓸 수 있는 열들인지.
 * 부호가 뒤집히는 값(순매수)은 100을 기준으로 나누면 방향이 뒤집혀 거짓말이 된다.
 */
export function canIndexSeries(rows: TableRow[], keys: string[]): boolean {
    if (keys.length < 2) return false;
    return keys.every(k => {
        const values = columnValues(rows, k);
        return values.length >= 2 && values.every(v => v > 0);
    });
}
