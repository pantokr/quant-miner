"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface FetchState<T> {
    data: T;
    loading: boolean;
    error: Error | null;
    /** 같은 URL을 다시 요청한다 (새로고침 버튼용) */
    reload: () => void;
}

/**
 * URL이 바뀌거나 reload()를 부를 때 요청하는 단순 fetch 훅.
 * url이 null이면 요청하지 않고 fallback을 반환한다.
 *
 * fallback은 초기값/에러 시에만 사용되므로 내부에서 ref로 잡아 둠 — 호출자가 매 렌더 새로운
 * 객체(예: [])를 넘겨도 effect가 재실행되지 않는다.
 *
 * 재요청이 두 종류라 화면 처리가 다르다.
 *   - URL이 바뀐 경우(= 다른 종목) : 이전 데이터를 버린다. 남겨 두면 새 종목을 고른 뒤에도
 *     잠깐 이전 종목의 그래프가 보여서 그게 새 종목 데이터인 줄 오해하게 된다.
 *     호출부는 data가 빈 동안 로딩 인디케이터를 띄우면 된다.
 *   - 같은 URL 재조회(새로고침 버튼·주기 갱신) : 데이터를 그대로 들고 있는다.
 *     화면이 깜빡이지 않고 응답이 오면 조용히 교체된다.
 *
 * refreshMs > 0이면 그 주기로 다시 받아온다(장중 분봉이 페이지를 연 시각에서 멈추는 문제 대응).
 */
export function useFetch<T>(url: string | null, fallback: T, refreshMs = 0): FetchState<T> {
    const fallbackRef = useRef(fallback);
    fallbackRef.current = fallback;

    // 지금 state.data가 어느 URL의 결과인지 — effect 안에서만 읽고 쓴다
    const loadedUrl = useRef<string | null>(null);

    const [nonce, setNonce] = useState(0);
    const [state, setState] = useState<Omit<FetchState<T>, "reload">>({
        data: fallback,
        loading: false,
        error: null,
    });

    const reload = useCallback(() => setNonce(n => n + 1), []);

    useEffect(() => {
        if (!url) {
            loadedUrl.current = null;
            setState({ data: fallbackRef.current, loading: false, error: null });
            return;
        }
        let cancelled = false;
        const sameUrl = loadedUrl.current === url;
        loadedUrl.current = url;
        setState(s => sameUrl
            ? { ...s, loading: true, error: null }
            : { data: fallbackRef.current, loading: true, error: null });
        fetch(url, { cache: "no-store" })
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then(data => {
                if (!cancelled) setState({ data, loading: false, error: null });
            })
            .catch(err => {
                if (!cancelled) {
                    console.error(err);
                    // 주기 갱신이 한 번 실패했다고 화면의 데이터를 버리지는 않는다.
                    setState(s => ({ ...s, loading: false, error: err }));
                }
            });
        return () => { cancelled = true; };
    }, [url, nonce]);

    useEffect(() => {
        if (!url || refreshMs <= 0) return;
        const timer = setInterval(() => setNonce(n => n + 1), refreshMs);
        return () => clearInterval(timer);
    }, [url, refreshMs]);

    return { ...state, reload };
}
