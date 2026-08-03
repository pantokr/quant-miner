"use client";

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
    ReferenceLine,
    ResponsiveContainer,
    Scatter,
    ScatterChart,
    Tooltip,
    XAxis,
    YAxis,
    ZAxis,
} from "recharts";
import { useDarkMode } from "@/hooks/useDarkMode";
import { CHROME_DARK, CHROME_LIGHT, seriesColor } from "@/lib/viz-palette";
import { CandleDatum, CandleShape, CandleTooltip } from "@/components/charts/Candle";
import { buildYScale } from "./axisScale";
import { TableRow, toNumber } from "./parseTable";

export type ChartKind = "line" | "bar" | "area" | "scatter" | "candle";

/**
 * Y축 처리 방식.
 *
 * shared   — 눈금 하나. 실제 크기를 그대로 견준다(기본).
 * separate — 시리즈마다 제 최소~최대에 맞춘 축. 크기는 버리고 모양만 견준다.
 * index    — 첫 값을 100으로 놓은 지수. 같은 기준 대비 등락을 한 축에서 견준다.
 */
export type YMode = "shared" | "separate" | "index";

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
    /** 자릿수가 다른 열을 견주는 방식 (기본 shared) */
    yMode?: YMode;
}

/** 지수 환산 뒤에도 원래 값을 툴팁에 보여 주려고 같은 행에 숨겨 둔다 */
const RAW_PREFIX = "__raw:";

/**
 * 개별 축으로 그릴 수 있는 시리즈 수.
 *
 * 축 자리는 그림 왼쪽·오른쪽 둘뿐이다. 셋째부터는 눈금을 놓을 자리가 없어
 * 축 없는 선이 되는데, 그러면 어느 스케일로 그려졌는지 읽을 방법이 사라진다.
 * 그래서 개별 축은 2개까지만 받는다 (호출부가 미리 잘라서 넘긴다).
 */
export const MAX_SEPARATE_AXES = 2;

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

    // 봉 전체가 들어오도록 저가·고가를 다 넣는다. 0에 묶지 않는다 — 주가는 변동 폭이 곧 정보다.
    const scale = buildYScale(
        data.flatMap(d => [d.low, d.high]),
        { includeZero: false },
    );

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
                        domain={scale?.domain}
                        ticks={scale?.ticks}
                        tickFormatter={scale?.format}
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

export function ChartCanvas({ kind, rows, xKey, yKeys, sortByValue, ohlc, yMode = "shared" }: Props) {
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

    // 지수 환산 — 각 시리즈를 제 첫 유효값으로 나눠 100에서 출발시킨다.
    // 축을 나누지 않고도 자릿수가 다른 열의 등락률을 한 눈금 위에서 견줄 수 있다.
    if (yMode === "index") {
        const base: Record<string, number> = {};
        yKeys.forEach(k => {
            const first = data.find(p => typeof p[k] === "number" && p[k] !== 0);
            if (first) base[k] = Number(first[k]);
        });
        data = data.map(p => {
            const next = { ...p };
            yKeys.forEach(k => {
                const v = p[k];
                next[`${RAW_PREFIX}${k}`] = v;
                next[k] = typeof v === "number" && base[k] ? (v / base[k]) * 100 : null;
            });
            return next;
        });
    }

    const seriesValues = (keys: string[]) => {
        const out: number[] = [];
        data.forEach(p => keys.forEach(k => {
            const v = p[k];
            if (typeof v === "number") out.push(v);
        }));
        return out;
    };

    const includeZero = kind === "bar";

    /**
     * 개별 축 — 시리즈마다 제 값만 보고 축을 잡는다. 각자 제 범위를 꽉 채워 그려지므로
     * 크기 차이가 사라지고 모양(오르내린 자리)만 남는다. 좌·우 두 자리가 상한이다.
     */
    const separate = yMode === "separate";

    /** 실제로 그릴 시리즈 — 개별 축은 눈금을 놓을 자리가 없는 셋째부터 그리지 않는다 */
    const drawnKeys = separate ? yKeys.slice(0, MAX_SEPARATE_AXES) : yKeys;

    // 축을 데이터가 놓인 구간에 맞춘다. 막대만 0을 지킨다 — 막대는 길이가 곧 크기라
    // 바닥을 잘라 내면 차이가 부풀려진다.
    const scale = buildYScale(seriesValues(drawnKeys), { includeZero });
    const perSeries = separate
        ? drawnKeys.map(k => buildYScale(seriesValues([k]), { includeZero }))
        : null;

    /** 시리즈가 붙을 축 id — 공통 축이면 전부 같은 축을 쓴다 */
    const axisIdOf = (key: string) => (perSeries ? key : 0);

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
            {perSeries ? (
                // 눈금을 시리즈 색으로 칠한다 — 어느 축이 어느 선의 것인지가 색으로 붙는다
                drawnKeys.map((k, i) => (
                    <YAxis
                        key={k}
                        yAxisId={k}
                        orientation={i === 0 ? "left" : "right"}
                        tick={{ ...axisTick, fill: seriesColor(i, dark) }}
                        tickLine={false}
                        axisLine={false}
                        width="auto"
                        tickMargin={6}
                        domain={perSeries[i]?.domain}
                        ticks={perSeries[i]?.ticks}
                        tickFormatter={perSeries[i]?.format}
                    />
                ))
            ) : (
                <YAxis
                    tick={axisTick}
                    tickLine={false}
                    axisLine={false}
                    width="auto"
                    tickMargin={6}
                    domain={scale?.domain}
                    ticks={scale?.ticks}
                    tickFormatter={scale?.format}
                />
            )}
            {/* 지수 비교의 출발선 — 100 위/아래가 곧 기준 대비 등락이다 */}
            {yMode === "index" && <ReferenceLine y={100} stroke={chrome.axis} strokeWidth={1} />}
            <Tooltip
                contentStyle={tooltipStyle}
                cursor={{ stroke: chrome.axis, strokeWidth: 1 }}
                labelFormatter={v => String(v ?? "")}
                formatter={(v, name, item) => {
                    const label = String(name ?? "");
                    if (yMode !== "index") return [Number(v).toLocaleString(), label];
                    // 지수만 보면 실제 규모를 알 수 없으므로 원래 값을 괄호로 함께 준다
                    const raw = (item?.payload as Record<string, unknown> | undefined)?.[`${RAW_PREFIX}${label}`];
                    const rawText = typeof raw === "number" ? ` (${raw.toLocaleString()})` : "";
                    return [`${Number(v).toFixed(1)}${rawText}`, label];
                }}
            />
            {/* 시리즈가 2개 이상이면 범례는 항상 — 정체성이 색에만 실리지 않도록 */}
            {drawnKeys.length > 1 && (
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
                        {drawnKeys.map((k, i) => (
                            <Line
                                key={k}
                                type="monotone"
                                dataKey={k}
                                yAxisId={axisIdOf(k)}
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
                            {drawnKeys.map((k, i) => (
                                <linearGradient key={k} id={`vizfill-${i}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={seriesColor(i, dark)} stopOpacity={0.28} />
                                    <stop offset="95%" stopColor={seriesColor(i, dark)} stopOpacity={0.02} />
                                </linearGradient>
                            ))}
                        </defs>
                        {common}
                        {drawnKeys.map((k, i) => (
                            <Area
                                key={k}
                                type="monotone"
                                dataKey={k}
                                yAxisId={axisIdOf(k)}
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
                        {drawnKeys.map((k, i) => (
                            <Bar
                                key={k}
                                dataKey={k}
                                yAxisId={axisIdOf(k)}
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
                        {drawnKeys.map((k, i) => (
                            <Scatter
                                key={k}
                                name={k}
                                data={data.filter(p => p[k] !== null)}
                                dataKey={k}
                                yAxisId={axisIdOf(k)}
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
