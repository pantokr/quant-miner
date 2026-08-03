"use client";

import { useSyncExternalStore } from "react";

/**
 * 다크 모드 여부.
 *
 * 테마는 React 밖(문서 루트 속성 + OS 설정)에 있으므로 useSyncExternalStore로 구독한다.
 * 토글이 data-theme을 찍으면 즉시 반영된다. 차트는 색을 직접 계산해 넘기므로
 * (CSS 변수로는 canvas/SVG 팔레트를 고를 수 없다) 이 값이 필요하다.
 */
function subscribe(onChange: () => void): () => void {
    const observer = new MutationObserver(onChange);
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-theme", "class"],
    });
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", onChange);
    return () => { observer.disconnect(); media.removeEventListener("change", onChange); };
}

function read(): boolean {
    const stamped = document.documentElement.getAttribute("data-theme");
    if (stamped === "dark") return true;
    if (stamped === "light") return false;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function useDarkMode(): boolean {
    // 서버 렌더에서는 라이트로 그린 뒤 하이드레이션 때 실제 값으로 맞춘다
    return useSyncExternalStore(subscribe, read, () => false);
}
