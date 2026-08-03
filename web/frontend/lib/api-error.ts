/**
 * FastAPI 오류 본문에서 사람이 읽을 메시지 뽑기.
 *
 * web/backend는 게이트웨이 응답 본문을 통째로 detail에 담아 중계하므로 detail이 다시
 * `{"detail": "..."}` JSON 문자열인 경우가 있다. 사용자에게는 가장 안쪽 메시지만 보인다.
 */
export function extractDetail(body: string, status: number): string {
    let current: unknown = body;
    for (let depth = 0; depth < 3; depth++) {
        if (typeof current !== "string") break;
        try {
            const parsed = JSON.parse(current);
            const detail = (parsed as { detail?: unknown })?.detail;
            if (detail === undefined) break;
            current = detail;
        } catch {
            break;
        }
    }
    if (typeof current === "string" && current.trim()) return current.trim();
    return body.trim() ? body.slice(0, 200) : `HTTP ${status}`;
}

/**
 * JSON을 받아오되 실패하면 읽을 수 있는 오류로 던진다.
 *
 * 화면이 조용히 비는 것이 가장 나쁘다 — 서버가 404를 주는 것과 계좌에 잔고가 없는 것은
 * 사용자에게 완전히 다른 상황인데, 아무 말이 없으면 둘을 구분할 수 없다.
 */
export async function fetchJson<T>(url: string): Promise<T> {
    const res = await fetch(url, { cache: "no-store" });
    const body = await res.text();
    if (!res.ok) throw new Error(extractDetail(body, res.status));
    return body ? (JSON.parse(body) as T) : (null as T);
}
