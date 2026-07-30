/**
 * 종목 검색 클라이언트.
 *
 * 검색 대상은 서버의 `stock_master` 테이블(KIS 마스터 파일 적재분, 약 3,500종목)이다.
 * 적재는 `scripts/load_stock_master.py`가 담당하므로 프론트에 종목 목록을 두지 않는다.
 */
import { MASTER_API } from "./api-config";

export interface MasterStock {
    stock_code: string;
    name: string;
    market: string;      // KOSPI | KOSDAQ
    isin?: string | null;
}

const CODE_RE = /^\d{6}$/;

export function isStockCode(q: string): boolean {
    return CODE_RE.test(q.trim());
}

async function getJson(url: string, signal?: AbortSignal): Promise<MasterStock[]> {
    const res = await fetch(url, { cache: "no-store", signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const body = await res.json();
    return Array.isArray(body) ? body : [];
}

/** 종목명·코드 부분 일치 검색. */
export function searchStocks(query: string, signal?: AbortSignal, limit = 15): Promise<MasterStock[]> {
    const q = query.trim();
    if (!q) return Promise.resolve([]);
    return getJson(`${MASTER_API.SEARCH}?q=${encodeURIComponent(q)}&limit=${limit}`, signal);
}

/** 종목코드 여러 개를 한 번에 조회 (인기 종목 칩 등). */
export function stocksByCodes(codes: string[], signal?: AbortSignal): Promise<MasterStock[]> {
    if (!codes.length) return Promise.resolve([]);
    return getJson(`${MASTER_API.SEARCH}?codes=${codes.join(",")}`, signal);
}
