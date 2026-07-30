import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

/**
 * 앱 테마 — 차분한 무채색(slate) 계열.
 *
 * 강조색을 빨강·파랑에서 떼어 놓은 이유: 이 앱에서 빨강은 상승, 파랑은 하락이라는
 * 고정된 의미를 이미 갖고 있다. 강조색이 그 둘 중 하나에 가까우면 "선택됨"과
 * "올랐음/내렸음"이 섞여 읽힌다. 그래서 채도가 낮은 slate를 강조색으로 쓴다.
 *
 * 색을 바꾸고 싶으면 아래 accent 스케일만 손대면 전체가 따라 바뀐다.
 */
const accent = {
    50: { value: "#f8fafc" },
    100: { value: "#f1f5f9" },
    200: { value: "#e2e8f0" },
    300: { value: "#cbd5e1" },
    400: { value: "#94a3b8" },
    500: { value: "#475569" },
    600: { value: "#334155" },
    700: { value: "#1e293b" },
    800: { value: "#0f172a" },
    900: { value: "#020617" },
    950: { value: "#010309" },
};

const config = defineConfig({
    theme: {
        tokens: {
            colors: { accent },
        },
        semanticTokens: {
            colors: {
                accent: {
                    // colorPalette="accent" 로 쓸 때 필요한 역할별 토큰
                    contrast: {
                        value: { _light: "white", _dark: "white" },
                    },
                    fg: {
                        value: { _light: "{colors.accent.600}", _dark: "{colors.accent.300}" },
                    },
                    subtle: {
                        value: { _light: "{colors.accent.100}", _dark: "{colors.accent.800}" },
                    },
                    muted: {
                        value: { _light: "{colors.accent.200}", _dark: "{colors.accent.700}" },
                    },
                    emphasized: {
                        value: { _light: "{colors.accent.300}", _dark: "{colors.accent.600}" },
                    },
                    solid: {
                        value: { _light: "{colors.accent.600}", _dark: "{colors.accent.500}" },
                    },
                    focusRing: {
                        value: { _light: "{colors.accent.500}", _dark: "{colors.accent.400}" },
                    },
                },
            },
        },
    },
});

export const system = createSystem(defaultConfig, config);

/** 차트·SVG처럼 토큰을 못 쓰는 곳에서 쓸 원시 색상값 */
export const ACCENT_HEX = {
    solid: "#334155",
    solidDark: "#475569",
    muted: "#94a3b8",
    line: "#64748b",
};
