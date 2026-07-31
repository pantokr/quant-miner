"use client";

import { useEffect, useRef, useState } from "react";

const PREFIX = "quant-miner:";

/**
 * 새로고침(F5)해도 값이 남는 상태.
 *
 * - 서버 렌더 시점에는 저장소가 없으므로 첫 렌더는 항상 initial로 그리고,
 *   마운트 직후 저장된 값으로 덮어쓴다(하이드레이션 불일치 방지).
 * - sessionStorage를 쓴다 — 새로고침·뒤로가기에는 남고, 탭을 닫으면 사라져서
 *   다음에 새로 열 땐 기본 화면에서 시작한다.
 */
export function usePersistentState<T>(key: string, initial: T) {
    const storageKey = PREFIX + key;
    const [value, setValue] = useState<T>(initial);

    // 복원 전에 initial을 저장해서 저장값을 덮어쓰는 일이 없도록 첫 실행은 건너뛴다.
    const skipFirstSave = useRef(true);

    useEffect(() => {
        try {
            const raw = window.sessionStorage.getItem(storageKey);
            // eslint-disable-next-line react-hooks/set-state-in-effect
            if (raw !== null) setValue(JSON.parse(raw) as T);
        } catch {
            /* 저장소를 못 쓰거나 값이 깨졌으면 기본값으로 둔다 */
        }
    }, [storageKey]);

    useEffect(() => {
        if (skipFirstSave.current) {
            skipFirstSave.current = false;
            return;
        }
        try {
            window.sessionStorage.setItem(storageKey, JSON.stringify(value));
        } catch {
            /* 용량 초과 등은 무시 — 저장 실패해도 화면은 정상 동작한다 */
        }
    }, [storageKey, value]);

    return [value, setValue] as const;
}
