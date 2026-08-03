/**
 * 조회 기간(YYYYMMDD) 계산.
 *
 * datasets.ts에서 떼어 뒀다 — 저기는 아이콘·API 설정을 끌어와서 순수 함수만 따로
 * 시험해 보기가 어렵다. 여기 함수들은 문자열만 주고받는다.
 */

export function ymd(date: Date): string {
    return `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, "0")}${String(date.getDate()).padStart(2, "0")}`;
}

export function daysAgo(days: number): string {
    const d = new Date();
    d.setDate(d.getDate() - days);
    return ymd(d);
}

function parseYmd(s: string): Date {
    return new Date(Number(s.slice(0, 4)), Number(s.slice(4, 6)) - 1, Number(s.slice(6, 8)));
}

/** 이보다 과거로는 넓히지 않는다 — KIS도 이 아래로는 거의 주지 않는다 */
export const EARLIEST = "19900101";

/**
 * 조회 기간을 과거로 넓힌다 — 지금 구간만큼 더 뒤로 물린다(최소 30일).
 *
 * 한 번에 구간이 두 배가 되므로 1년으로 시작하면 여섯 번이면 60년치에 닿는다.
 * 표를 채울 행이 모자랄 때, 사용자가 날짜를 손대지 않고도 더 받아오게 하는 데 쓴다.
 */
export function widenStart(start: string, end: string): string {
    const from = parseYmd(start);
    const to = parseYmd(end);
    const span = Math.max(30, Math.round((to.getTime() - from.getTime()) / 86_400_000));
    const next = new Date(from);
    next.setDate(next.getDate() - span);
    return next < parseYmd(EARLIEST) ? EARLIEST : ymd(next);
}

/** 더 넓힐 여지가 남았는지 */
export function canWiden(start: string): boolean {
    return start > EARLIEST;
}
