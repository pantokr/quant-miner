"use client";

import { useEffect, useRef, useState } from "react";

export interface FetchState<T> {
    data: T;
    loading: boolean;
    error: Error | null;
}

/**
 * URL이 바뀔 때만 다시 요청하는 단순 fetch 훅.
 * url이 null이면 요청하지 않고 fallback을 반환한다.
 *
 * fallback은 초기값/에러 시에만 사용되므로 내부에서 ref로 잡아 둠 — 호출자가 매 렌더 새로운
 * 객체(예: [])를 넘겨도 effect가 재실행되지 않는다.
 */
export function useFetch<T>(url: string | null, fallback: T): FetchState<T> {
    const fallbackRef = useRef(fallback);
    fallbackRef.current = fallback;

    const [state, setState] = useState<FetchState<T>>({ data: fallback, loading: false, error: null });

    useEffect(() => {
        if (!url) {
            setState({ data: fallbackRef.current, loading: false, error: null });
            return;
        }
        let cancelled = false;
        setState(s => ({ ...s, loading: true, error: null }));
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
                    setState({ data: fallbackRef.current, loading: false, error: err });
                }
            });
        return () => { cancelled = true; };
    }, [url]);

    return state;
}
