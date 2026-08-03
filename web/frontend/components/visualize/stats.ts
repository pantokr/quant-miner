/**
 * 두 열이 실제로 비례하는지 숫자로 답한다.
 *
 * 개별 축(시리즈마다 제 범위로 늘려 그리기)은 모양을 견주기엔 좋지만, 두 축을 맞추는
 * 기준이 임의라 눈으로만 보면 없는 상관관계도 있어 보인다. 그래서 축을 나눠 그릴 때는
 * 상관계수를 함께 띄워 "닮아 보인다"와 "닮았다"를 갈라 준다.
 */
import { TableRow, toNumber } from "./parseTable";

/** 같은 행에서 두 열이 모두 숫자인 쌍만 모은다 */
function pairedValues(rows: TableRow[], a: string, b: string): [number[], number[]] {
    const xs: number[] = [];
    const ys: number[] = [];
    for (const r of rows) {
        const x = toNumber(r[a]);
        const y = toNumber(r[b]);
        if (x === null || y === null) continue;
        xs.push(x);
        ys.push(y);
    }
    return [xs, ys];
}

/** 피어슨 상관계수. 쌍이 3개 미만이거나 한쪽이 상수면 계산하지 않는다. */
export function correlation(rows: TableRow[], a: string, b: string): number | null {
    const [xs, ys] = pairedValues(rows, a, b);
    const n = xs.length;
    if (n < 3) return null;

    const meanX = xs.reduce((s, v) => s + v, 0) / n;
    const meanY = ys.reduce((s, v) => s + v, 0) / n;

    let cov = 0;
    let varX = 0;
    let varY = 0;
    for (let i = 0; i < n; i++) {
        const dx = xs[i] - meanX;
        const dy = ys[i] - meanY;
        cov += dx * dy;
        varX += dx * dx;
        varY += dy * dy;
    }
    if (varX === 0 || varY === 0) return null;

    const r = cov / Math.sqrt(varX * varY);
    // 부동소수 오차로 ±1을 살짝 넘는 경우가 있다
    return Math.max(-1, Math.min(1, r));
}

/** 상관계수를 말로 옮긴다 — 숫자만 보면 0.4가 센지 약한지 판단이 갈린다 */
export function correlationLabel(r: number): string {
    const abs = Math.abs(r);
    const direction = r >= 0 ? "비례" : "역비례";
    if (abs < 0.2) return "관계 거의 없음";
    if (abs < 0.4) return `약한 ${direction}`;
    if (abs < 0.7) return `뚜렷한 ${direction}`;
    return `강한 ${direction}`;
}
