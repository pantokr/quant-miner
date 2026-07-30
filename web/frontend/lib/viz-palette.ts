/**
 * 차트 팔레트 — validate_palette.js 로 두 모드 모두 검증한 값.
 *
 *   light: 인접쌍 CVD ΔE 9.1 / 일반시야 ΔE 19.6 · contrast WARN(3슬롯 <3:1)
 *   dark : 인접쌍 CVD ΔE 8.4 / 일반시야 ΔE 19.3 · contrast 전부 ≥3:1
 *
 * 라이트 모드의 contrast WARN은 "표를 함께 제공"으로 해소한다(시각화 페이지는
 * 항상 원본 표를 같이 띄운다). 슬롯 순서 자체가 CVD 안전장치이므로 순환·재정렬 금지.
 */
export const CATEGORICAL_LIGHT = [
    "#2a78d6", // 1 blue
    "#eb6834", // 2 orange
    "#1baf7a", // 3 aqua
    "#eda100", // 4 yellow
    "#e87ba4", // 5 magenta
    "#008300", // 6 green
    "#4a3aa7", // 7 violet
    "#e34948", // 8 red
] as const;

export const CATEGORICAL_DARK = [
    "#3987e5",
    "#d95926",
    "#199e70",
    "#c98500",
    "#d55181",
    "#008300",
    "#9085e9",
    "#e66767",
] as const;

/** 색만으로 8개를 구분할 수 있는 상한. 넘으면 시리즈를 줄이거나 나눠 그린다. */
export const MAX_SERIES = 8;

/**
 * 산점도는 모든 쌍이 동시에 보이므로(all-pairs) 3개까지만 게이트를 통과한다.
 * 4번째부터 노랑과 주황이 함께 놓여 일반시야 floor가 깨진다.
 */
export const MAX_SERIES_ALL_PAIRS = 3;

export const CHROME_LIGHT = {
    surface: "#fcfcfb",
    grid: "#e1e0d9",
    axis: "#c3c2b7",
    muted: "#898781",
    text: "#0b0b0b",
    textSecondary: "#52514e",
};

export const CHROME_DARK = {
    surface: "#1a1a19",
    grid: "#2c2c2a",
    axis: "#383835",
    muted: "#898781",
    text: "#ffffff",
    textSecondary: "#c3c2b7",
};

export function seriesColor(index: number, dark: boolean): string {
    const ramp = dark ? CATEGORICAL_DARK : CATEGORICAL_LIGHT;
    // 순환하지 않는다 — 상한을 넘으면 마지막 슬롯에 머문다(UI가 미리 막는다).
    return ramp[Math.min(index, ramp.length - 1)];
}
