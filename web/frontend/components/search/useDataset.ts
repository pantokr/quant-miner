"use client";

import { useEffect, useState } from "react";

interface Loaded {
    /** 이 결과를 만들어 낸 요청 URL — 현재 url과 다르면 아직 로딩 중이라는 뜻 */
    url: string | null;
    data: unknown;
    /** 사용자에게 보여줄 오류 메시지 (FastAPI의 detail을 우선 사용) */
    error: string | null;
    fetchedAt: Date | null;
}

export interface DatasetState {
    data: unknown;
    loading: boolean;
    /** 화면에 보이는 값이 직전 조회 결과이고 새 결과를 기다리는 중 */
    stale: boolean;
    error: string | null;
    fetchedAt: Date | null;
}

const EMPTY: Loaded = { url: null, data: null, error: null, fetchedAt: null };

/**
 * FastAPI detail 추출.
 *
 * web/backend는 게이트웨이 응답 본문을 통째로 detail에 담아 중계하므로 detail이 다시
 * `{"detail": "..."}` JSON 문자열인 경우가 있다. 사용자에게는 가장 안쪽 메시지만 보인다.
 */
function extractDetail(body: string, status: number): string {
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
 * 조회 URL이 바뀔 때만 요청하는 훅.
 *
 * `useFetch`와 달리 FastAPI가 내려주는 `detail` 본문을 파싱해 오류 메시지로 노출한다.
 * KIS 계정 권한/모의투자 제약 때문에 실패하는 엔드포인트가 있어, 원인을 표에서 바로
 * 확인할 수 있어야 하기 때문이다.
 *
 * loading은 별도 state가 아니라 "결과의 url이 아직 현재 url이 아님"으로 파생시킨다.
 */
export function useDataset(url: string): DatasetState {
    const [loaded, setLoaded] = useState<Loaded>(EMPTY);

    useEffect(() => {
        let cancelled = false;

        fetch(url, { cache: "no-store" })
            .then(async res => {
                const body = await res.text();
                if (!res.ok) throw new Error(extractDetail(body, res.status));
                return body ? JSON.parse(body) : null;
            })
            .then(data => {
                if (!cancelled) setLoaded({ url, data, error: null, fetchedAt: new Date() });
            })
            .catch(err => {
                if (!cancelled) {
                    setLoaded({
                        url,
                        data: null,
                        error: err instanceof Error ? err.message : String(err),
                        fetchedAt: new Date(),
                    });
                }
            });

        return () => { cancelled = true; };
    }, [url]);

    // stale-while-revalidate: 새 요청이 도는 동안에도 직전 결과를 그대로 돌려준다.
    // 표가 비었다가 다시 그려지지 않고, 응답이 도착하면 그 자리에서 값만 교체된다.
    const fresh = loaded.url === url;
    return {
        data: loaded.data,
        loading: !fresh,
        stale: !fresh && loaded.url !== null,
        error: fresh ? loaded.error : null,
        fetchedAt: loaded.fetchedAt,
    };
}
