"use client";

import { useSyncExternalStore } from "react";
import { Box, Text } from "@chakra-ui/react";
import {
    Area,
    AreaChart,
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Scatter,
    ScatterChart,
    Tooltip,
    XAxis,
    YAxis,
    ZAxis,
} from "recharts";
import { CHROME_DARK, CHROME_LIGHT, seriesColor } from "@/lib/viz-palette";
import { CandleDatum, CandleShape, CandleTooltip } from "@/components/charts/Candle";
import { TableRow, toNumber } from "./parseTable";

export type ChartKind = "line" | "bar" | "area" | "scatter" | "candle";

/** 축 라벨이 잘리지 않도록 사방에 여백을 둔다 (특히 아래·오른쪽). */
const CHART_MARGIN = { top: 8, right: 32, left: 10, bottom: 10 };

/** 캔들에 쓸 시·고·저·종가 열 */
export interface OhlcKeys {
    open: string;
    high: string;
    low: string;
    close: string;
}

interface Props {
    kind: ChartKind;
    rows: TableRow[];
    xKey: string;
    yKeys: string[];
    /** 값이 큰 순으로 정렬 (막대 그래프에서 크기 비교가 쉬워진다) */
    sortByValue?: boolean;
    /** kind="candle"일 때 쓸 O/H/L/C 열 */
    ohlc?: OhlcKeys | null;
}

/**
 * 다크 모드 여부 — 테마는 React 밖(문서 루트 속성 + OS 설정)에 있으므로
 * useSyncExternalStore로 구독한다. 토글이 data-theme을 찍으면 즉시 반영된다.
 */
function subscribeToTheme(onChange: () => void): () => void {
    const observer = new MutationObserver(onChange);
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ["data-theme", "class"],
    });
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", onChange);
    return () => { observer.disconnect(); media.removeEventListener("change", onChange); };
}

function readTheme(): boolean {
    const stamped = document.documentElement.getAttribute("data-theme");
    if (stamped === "dark") return true;
    if (stamped === "light") return false;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function useDarkMode(): boolean {
    // 서버 렌더에서는 라이트로 그린 뒤 하이드레이션 때 실제 값으로 맞춘다
    return useSyncExternalStore(subscribeToTheme, readTheme, () => false);
}

/**
 * Y축 눈금 축약. 소수점을 버리고 자연수로만 표시해 라벨을 짧게 유지한다.
 * 예) 13,726,154,839,133 → "14조",  208,500 → "21만"
 */
function compact(v: number): string {
    const abs = Math.abs(v);
    if (abs >= 1e12) return `${Math.round(v / 1e12)}조`;
    if (abs >= 1e8) return `${Math.round(v / 1e8)}억`;
    if (abs >= 1e4) return `${Math.round(v / 1e4)}만`;
    // 비율·배수처럼 1 미만이 의미 있는 값은 소수 한 자리까지만
    if (abs > 0 && abs < 10) return String(Number(v.toFixed(1)));
    return String(Math.round(v));
}

/** X축 라벨 축약 — 20260729 → 07/29, 202612 → 26/12, 093000 → 09:30 */
function shortenX(raw: unknown): string {
    const s = String(raw ?? "");
    if (/^\d{8}$/.test(s)) return `${s.slice(4, 6)}/${s.slice(6, 8)}`;
    if (/^\d{6}$/.test(s)) {
        // HHMMSS(시각)와 YYYYMM(년월)이 둘 다 6자리 — 앞 두 자리로 구분
        const head = Number(s.slice(0, 2));
        return head <= 23 && Number(s.slice(2, 4)) <= 59 && s.slice(4) === "00"
            ? `${s.slice(0, 2)}:${s.slice(2, 4)}`
            : `${s.slice(2, 4)}/${s.slice(4, 6)}`;
    }
    return s.length > 10 ? `${s.slice(0, 9)}…` : s;
}

/** 캔들차트 — Bar를 [저가, 고가] 떠 있는 막대로 두고 custom shape로 봉을 그린다. */
function CandleCanvas({
    rows, xKey, ohlc, chrome,
}: {
    rows: TableRow[];
    xKey: string;
    ohlc?: OhlcKeys | null;
    chrome: typeof CHROME_LIGHT;
}) {
    if (!xKey || !ohlc?.open || !ohlc.high || !ohlc.low || !ohlc.close) {
        return <EmptyNote>캔들은 시가·고가·저가·종가 열이 모두 필요합니다.</EmptyNote>;
    }

    const data: CandleDatum[] = [];
    for (const r of rows) {
        const open = toNumber(r[ohlc.open]);
        const high = toNumber(r[ohlc.high]);
        const low = toNumber(r[ohlc.low]);
        const close = toNumber(r[ohlc.close]);
        if (open === null || high === null || low === null || close === null) continue;
        data.push({
            [xKey]: String(r[xKey] ?? ""),
            open, high, low, close,
            _range: [low, high],
        } as CandleDatum);
    }

    if (!data.length) {
        return <EmptyNote>선택한 열에서 시·고·저·종가 숫자를 찾지 못했습니다.</EmptyNote>;
    }

    const lows = data.map(d => d.low);
    const highs = data.map(d => d.high);
    const min = Math.min(...lows);
    const max = Math.max(...highs);
    const pad = (max - min) * 0.06 || Math.abs(max) * 0.02 || 1;

    const axisTick = { fill: chrome.muted, fontSize: 11, fontWeight: 600 };

    return (
        <Box
            h="420px" w="full"
            bg={chrome.surface}
            borderRadius="xl"
            borderWidth="1px"
            borderColor={chrome.grid}
            p={4}
        >
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={CHART_MARGIN} barCategoryGap="18%">
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={chrome.grid} />
                    <XAxis
                        dataKey={xKey}
                        tick={axisTick}
                        tickLine={false}
                        axisLine={{ stroke: chrome.axis }}
                        tickFormatter={shortenX}
                        tickMargin={8}
                        height={28}
                        minTickGap={28}
                    />
                    <YAxis
                        tick={axisTick}
                        tickLine={false}
                        axisLine={false}
                        width="auto"
                        tickMargin={6}
                        domain={[min - pad, max + pad]}
                        tickFormatter={(v: number) => compact(v)}
                    />
                    <Tooltip
                        cursor={{ fill: chrome.grid, opacity: 0.3 }}
                        content={(p) => (
                            <CandleTooltip
                                active={p.active}
                                payload={p.payload}
                                label={p.label}
                                surface={chrome.surface}
                                grid={chrome.grid}
                                text={chrome.text}
                            />
                        )}
                    />
                    <Bar dataKey="_range" shape={<CandleShape />} isAnimationActive={false} />
                </BarChart>
            </ResponsiveContainer>
        </Box>
    );
}

function EmptyNote({ children }: { children: React.ReactNode }) {
    return (
        <Box py={20} textAlign="center">
            <Text fontSize="sm" color="fg.subtle" fontWeight="medium">{children}</Text>
        </Box>
    );
}

export function ChartCanvas({ kind, rows, xKey, yKeys, sortByValue, ohlc }: Props) {
    const dark = useDarkMode();
    const chrome = dark ? CHROME_DARK : CHROME_LIGHT;

    if (kind === "candle") {
        return <CandleCanvas rows={rows} xKey={xKey} ohlc={ohlc} chrome={chrome} />;
    }

    if (!xKey || !yKeys.length) {
        return <EmptyNote>X축과 Y축 열을 선택하면 그래프가 그려집니다.</EmptyNote>;
    }

    // 숫자 변환 + 모든 Y가 비어 있는 행 제거
    let data = rows
        .map(r => {
            const point: Record<string, string | number | null> = { [xKey]: String(r[xKey] ?? "") };
            yKeys.forEach(k => { point[k] = toNumber(r[k]); });
            return point;
        })
        .filter(p => yKeys.some(k => p[k] !== null));

    if (sortByValue && yKeys.length) {
        const primary = yKeys[0];
        data = [...data].sort((a, b) => (Number(b[primary]) || 0) - (Number(a[primary]) || 0));
    }

    if (!data.length) {
        return <EmptyNote>선택한 Y축 열에서 숫자를 찾지 못했습니다. 다른 열을 선택해 보세요.</EmptyNote>;
    }

    const axisTick = { fill: chrome.muted, fontSize: 11, fontWeight: 600 };
    const tooltipStyle: React.CSSProperties = {
        borderRadius: 10,
        border: `1px solid ${chrome.grid}`,
        background: chrome.surface,
        color: chrome.text,
        fontSize: 12,
        fontWeight: 600,
        boxShadow: "0 10px 15px -3px rgba(0,0,0,0.12)",
    };

    // 축은 하나만 쓴다 — 스케일이 다른 두 지표를 한 차트에 겹치지 않는다.
    const common = (
        <>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={chrome.grid} />
            <XAxis
                dataKey={xKey}
                tick={axisTick}
                tickLine={false}
                axisLine={{ stroke: chrome.axis }}
                tickFormatter={shortenX}
                tickMargin={8}
                height={28}
                minTickGap={28}
                // 첫·끝 눈금 라벨이 그림 영역 밖으로 넘쳐 잘리지 않도록 좌우를 띄운다
                padding={{ left: 12, right: 12 }}
            />
            <YAxis
                tick={axisTick}
                tickLine={false}
                axisLine={false}
                width="auto"
                tickMargin={6}
                tickFormatter={(v: number) => compact(v)}
            />
            <Tooltip
                contentStyle={tooltipStyle}
                cursor={{ stroke: chrome.axis, strokeWidth: 1 }}
                labelFormatter={v => String(v ?? "")}
                formatter={(v, name) => [Number(v).toLocaleString(), String(name ?? "")]}
            />
            {/* 시리즈가 2개 이상이면 범례는 항상 — 정체성이 색에만 실리지 않도록 */}
            {yKeys.length > 1 && (
                <Legend
                    wrapperStyle={{ fontSize: 12, fontWeight: 700, color: chrome.textSecondary, paddingTop: 8 }}
                    iconType="circle"
                    iconSize={8}
                />
            )}
        </>
    );

    return (
        <Box
            h="420px"
            w="full"
            bg={chrome.surface}
            borderRadius="xl"
            borderWidth="1px"
            borderColor={chrome.grid}
            p={4}
        >
            <ResponsiveContainer width="100%" height="100%">
                {kind === "line" ? (
                    <LineChart data={data} margin={CHART_MARGIN}>
                        {common}
                        {yKeys.map((k, i) => (
                            <Line
                                key={k}
                                type="monotone"
                                dataKey={k}
                                stroke={seriesColor(i, dark)}
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 4, strokeWidth: 2, stroke: chrome.surface }}
                                isAnimationActive={false}
                                connectNulls
                            />
                        ))}
                    </LineChart>
                ) : kind === "area" ? (
                    <AreaChart data={data} margin={CHART_MARGIN}>
                        <defs>
                            {yKeys.map((k, i) => (
                                <linearGradient key={k} id={`vizfill-${i}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={seriesColor(i, dark)} stopOpacity={0.28} />
                                    <stop offset="95%" stopColor={seriesColor(i, dark)} stopOpacity={0.02} />
                                </linearGradient>
                            ))}
                        </defs>
                        {common}
                        {yKeys.map((k, i) => (
                            <Area
                                key={k}
                                type="monotone"
                                dataKey={k}
                                stroke={seriesColor(i, dark)}
                                strokeWidth={2}
                                fill={`url(#vizfill-${i})`}
                                isAnimationActive={false}
                                connectNulls
                            />
                        ))}
                    </AreaChart>
                ) : kind === "bar" ? (
                    <BarChart data={data} margin={CHART_MARGIN}>
                        {common}
                        {yKeys.map((k, i) => (
                            <Bar
                                key={k}
                                dataKey={k}
                                fill={seriesColor(i, dark)}
                                radius={[4, 4, 0, 0]}
                                isAnimationActive={false}
                            />
                        ))}
                    </BarChart>
                ) : (
                    <ScatterChart margin={CHART_MARGIN}>
                        {common}
                        <ZAxis range={[40, 40]} />
                        {yKeys.map((k, i) => (
                            <Scatter
                                key={k}
                                name={k}
                                data={data.filter(p => p[k] !== null)}
                                dataKey={k}
                                fill={seriesColor(i, dark)}
                                isAnimationActive={false}
                            />
                        ))}
                    </ScatterChart>
                )}
            </ResponsiveContainer>
        </Box>
    );
}
