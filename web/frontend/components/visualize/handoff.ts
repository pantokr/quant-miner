/**
 * 표 → 시각화 페이지 전달.
 *
 * 행 수가 많을 수 있어 URL이 아니라 sessionStorage로 넘긴다. /visualize가 마운트할 때
 * 한 번 읽고 지운다(뒤로 가기로 돌아와도 예전 표가 되살아나지 않도록).
 */
import { toNumber } from "./parseTable";

/** DataGrid의 GridRow와 파서의 TableRow를 모두 받도록 느슨하게 잡는다 (어차피 JSON 직렬화). */
export type HandoffRow = Record<string, unknown>;

export const HANDOFF_KEY = "quant-miner:viz-payload";

/** sessionStorage 할당량을 넘기지 않도록 두는 상한. 넘으면 앞에서부터 자른다. */
const MAX_ROWS = 20_000;
const FALLBACK_ROWS = 5_000;

export interface HandoffResult {
    ok: boolean;
    /** 실제로 넘긴 행 수 */
    sent: number;
    /** 상한 때문에 잘렸으면 원래 행 수 */
    truncatedFrom?: number;
    error?: string;
}

function write(label: string, rows: unknown[]): boolean {
    try {
        sessionStorage.setItem(HANDOFF_KEY, JSON.stringify({ label, rows }));
        return true;
    } catch {
        return false;
    }
}

export function sendToVisualize(label: string, rows: HandoffRow[]): HandoffResult {
    if (!rows.length) return { ok: false, sent: 0, error: "넘길 데이터가 없습니다." };

    const capped = rows.length > MAX_ROWS ? rows.slice(0, MAX_ROWS) : rows;
    if (write(label, capped)) {
        return {
            ok: true,
            sent: capped.length,
            truncatedFrom: capped.length < rows.length ? rows.length : undefined,
        };
    }

    // 용량 초과 — 더 작게 잘라 한 번 더 시도
    const smaller = rows.slice(0, FALLBACK_ROWS);
    if (write(label, smaller)) {
        return { ok: true, sent: smaller.length, truncatedFrom: rows.length };
    }
    return { ok: false, sent: 0, error: "데이터가 너무 커서 넘기지 못했습니다. 조회 기간을 줄여 주세요." };
}

/**
 * 그래프로 그릴 수 있는 표인지 — 숫자 열이 하나라도 있어야 한다.
 * (종목 기본정보처럼 항목/값 텍스트만 있는 표는 그릴 것이 없다)
 */
export function hasNumericColumn(rows: HandoffRow[]): boolean {
    if (!rows.length) return false;
    const keys = Object.keys(rows[0]);
    const sample = rows.slice(0, 30);
    return keys.some(key => {
        const values = sample.map(r => r[key]).filter(v => v !== null && v !== "");
        if (!values.length) return false;
        return values.filter(v => toNumber(v) !== null).length / values.length >= 0.8;
    });
}
