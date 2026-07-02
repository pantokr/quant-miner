import { OHLCVItem } from "@/types/stock";
import { OhlcvPeriod } from "./constants";

// 균등 간격 tick 계산 + 연도 경계에서 yyyy/mm/dd 표시
// 작은 데이터 길이에서 step이 1이 되어 모든 tick이 출력되는 문제 방지를 위해 ceil 사용
export function computeOhlcvTicks(
    data: OHLCVItem[],
    maxTicks: number,
    fmt: (date: string, showYear: boolean) => string,
): { ticks: string[]; labelMap: Record<string, string> } {
    if (!data.length) return { ticks: [], labelMap: {} };
    const step = Math.max(1, Math.ceil((data.length - 1) / Math.max(1, maxTicks - 1)));
    const indices = new Set<number>();
    for (let i = 0; i < data.length; i += step) indices.add(i);
    indices.add(data.length - 1);

    const ticks = [...indices].sort((a, b) => a - b).map(i => data[i].date);
    let prevYear = "";
    const labelMap: Record<string, string> = {};
    ticks.forEach(date => {
        const y = date.substring(0, 4);
        labelMap[date] = fmt(date, y !== prevYear);
        prevYear = y;
    });
    return { ticks, labelMap };
}

export function formatOhlcvDate(date: string, period: OhlcvPeriod, showYear: boolean): string {
    if (period === "yearly") return date.substring(0, 4);
    if (period === "monthly") return showYear ? `${date.substring(0, 4)}/${date.substring(4, 6)}` : date.substring(4, 6);
    return showYear
        ? `${date.substring(0, 4)}/${date.substring(4, 6)}/${date.substring(6, 8)}`
        : `${date.substring(4, 6)}/${date.substring(6, 8)}`;
}

export function formatOhlcvRangeLabel(date: string, period: OhlcvPeriod): string {
    if (period === "yearly") return date.substring(0, 4);
    if (period === "monthly") return `${date.substring(0, 4)}/${date.substring(4, 6)}`;
    return `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}`;
}

export function formatTimeNum(v: number): string {
    const s = String(v).padStart(6, "0");
    return `${s.substring(0, 2)}:${s.substring(2, 4)}`;
}

/**
 * 가격 시리즈의 Y축 도메인 계산.
 *
 * 슬라이스된 가격대가 평탄할 때 (예: 4998~5002) 자동맞춤으로 너무 좁게 잡혀
 * 패닝할 때마다 Y축이 급변하는 문제를 막기 위해, 중심값 기준 최소 폭을
 * 보장하고 작은 패딩을 추가한다.
 *
 * - minRangeRatio: 중심값 대비 최소로 보장할 (max-min) 비율 (기본 4%)
 * - paddingRatio: 최종 범위에 추가할 위/아래 여백 비율 (기본 5%)
 */
export function computeYDomain(
    values: number[],
    minRangeRatio = 0.04,
    paddingRatio = 0.05,
): [number, number] {
    const finite = values.filter(v => Number.isFinite(v));
    if (!finite.length) return [0, 100];

    let min = finite[0];
    let max = finite[0];
    for (const v of finite) {
        if (v < min) min = v;
        if (v > max) max = v;
    }

    const center = (min + max) / 2;
    const minRange = Math.abs(center) * minRangeRatio;
    if (max - min < minRange) {
        min = center - minRange / 2;
        max = center + minRange / 2;
    }

    const padding = (max - min) * paddingRatio;
    return [Math.max(0, min - padding), max + padding];
}
