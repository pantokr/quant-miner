"use client";

import { useEffect, useRef, useState } from "react";
import { Box, HStack, Spinner, Text, VStack } from "@chakra-ui/react";
import {
    Area,
    AreaChart,
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { STOCK_API } from "@/lib/api-config";
import { OHLCVItem, StockRankItem } from "@/types/stock";
import { CandleDatum, CandleShape, CandleTooltip } from "@/components/charts/Candle";
import {
    AXIS_TICK,
    CHART_MARGIN,
    ChartStyle,
    FIXED_WINDOW,
    GRAD_ID,
    MAX_TICKS,
    OhlcvPeriod,
    PAN_STEP,
    PERIOD_LABELS,
    TOOLTIP_STYLE,
    Y_TICK_MARGIN,
    compactPrice,
} from "./constants";
import {
    computeOhlcvTicks,
    computeYDomain,
    formatOhlcvDate,
    formatOhlcvRangeLabel,
} from "./utils";
import { useFetch } from "./useFetch";
import { RefreshButton } from "./RefreshButton";

const EMPTY_OHLCV: OHLCVItem[] = [];

interface Props {
    stock: StockRankItem;
    period: OhlcvPeriod;
    color: string;
    style: ChartStyle;
}

export function OhlcvChart({ stock, period, color, style }: Props) {
    const periodSuffix = period === "daily" ? "" : period === "monthly" ? "?period=M" : "?period=Y";
    const url = `${STOCK_API.OHLCV_ALL(stock.stock_code)}${periodSuffix}`;
    const { data, loading, reload } = useFetch<OHLCVItem[]>(url, EMPTY_OHLCV);

    const [offset, setOffset] = useState(0);
    const [dragStartX, setDragStartX] = useState<number | null>(null);
    const [dragStartOffset, setDragStartOffset] = useState<number | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // 기간/데이터 교체 시 가장 최근 구간으로 초기화
    useEffect(() => {
        setOffset(0);
        setDragStartX(null);
        setDragStartOffset(null);
    }, [period, data]);

    const winSize = FIXED_WINDOW[period];
    const maxOffset = Math.max(0, data.length - winSize);
    const safeOffset = Math.min(offset, maxOffset);
    const sliceEnd = data.length - safeOffset;
    const sliceStart = Math.max(0, sliceEnd - winSize);
    const visible = data.slice(sliceStart, sliceEnd);

    const canPanLeft = safeOffset < maxOffset;
    const canPanRight = safeOffset > 0;
    const panStep = PAN_STEP[period];

    const doPan = (dir: "left" | "right") =>
        setOffset(prev => Math.min(maxOffset, Math.max(0, prev + (dir === "left" ? panStep : -panStep))));

    const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!containerRef.current) return;
        setDragStartX(e.clientX);
        setDragStartOffset(safeOffset);
    };

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (dragStartX === null || dragStartOffset === null || !containerRef.current) return;
        e.preventDefault();
        const rect = containerRef.current.getBoundingClientRect();
        const itemWidth = rect.width / Math.max(1, winSize);
        const indexDelta = Math.round((e.clientX - dragStartX) / itemWidth);
        // 오른쪽으로 드래그(양수) → 더 과거 데이터 방향(offset 증가)
        setOffset(Math.max(0, Math.min(maxOffset, dragStartOffset + indexDelta)));
    };

    const handleMouseUp = () => {
        setDragStartX(null);
        setDragStartOffset(null);
    };

    const fmtDate = (date: string, showYear: boolean) => formatOhlcvDate(date, period, showYear);
    const visibleTicks = computeOhlcvTicks(visible, MAX_TICKS[period], fmtDate);
    const yDomain = computeYDomain(visible.map(d => d.close));

    // 캔들은 저가~고가 전체가 들어와야 하므로 도메인을 따로 잡는다
    const candleData: CandleDatum[] = visible.map(d => ({
        date: d.date,
        open: d.open, high: d.high, low: d.low, close: d.close,
        _range: [d.low, d.high],
    }));
    const candleDomain = candleData.length
        ? computeYDomain([
            ...candleData.map(d => d.low),
            ...candleData.map(d => d.high),
        ])
        : yDomain;

    const rangeLabel = visible.length >= 2
        ? `${formatOhlcvRangeLabel(visible[0].date, period)} ~ ${formatOhlcvRangeLabel(visible[visible.length - 1].date, period)}`
        : "";

    const widthLabel = period === "daily" ? `${winSize}일` : period === "monthly" ? `${winSize}개월` : `${winSize}년`;

    return (
        /* 탭 본문(TAB_BODY_H) 높이를 그대로 채운다 — 세 탭 크기를 맞추기 위함 */
        <VStack align="stretch" gap={2} flex="1" minH={0}>
            <VStack align="stretch" gap={2} px={1} flexShrink={0}>
                <HStack justify="space-between" align="center">
                    <Box
                        as="button"
                        px={2} py={0.5}
                        borderRadius="md"
                        fontSize="xs"
                        fontWeight="bold"
                        cursor={canPanLeft ? "pointer" : "not-allowed"}
                        opacity={canPanLeft ? 1 : 0.3}
                        bg="bg.muted"
                        color="fg.muted"
                        onClick={() => canPanLeft && doPan("left")}
                        userSelect="none"
                    >
                        ← 이전
                    </Box>
                    <Text fontSize="2xs" color="fg.subtle" fontWeight="medium">{rangeLabel}</Text>
                    <HStack gap={1.5}>
                        <Box
                            as="button"
                            px={2} py={0.5}
                            borderRadius="md"
                            fontSize="xs"
                            fontWeight="bold"
                            cursor={canPanRight ? "pointer" : "not-allowed"}
                            opacity={canPanRight ? 1 : 0.3}
                            bg="bg.muted"
                            color="fg.muted"
                            onClick={() => canPanRight && doPan("right")}
                            userSelect="none"
                        >
                            이후 →
                        </Box>
                        <RefreshButton onClick={reload} busy={loading} boxSize="22px" />
                    </HStack>
                </HStack>
                <Text fontSize="2xs" color="fg.muted" textAlign="center" fontWeight="medium">
                    💡 차트를 드래그하거나 마우스 휠로 기간을 이동하세요 ({widthLabel} 표시)
                </Text>
            </VStack>

            <Box
                ref={containerRef}
                flex="1"
                minH={0}
                w="100%"
                position="relative"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onWheel={(e) => {
                    e.preventDefault();
                    doPan(e.deltaY > 0 ? "left" : "right");
                }}
                cursor={dragStartX !== null ? "grabbing" : "grab"}
                userSelect="none"
            >
                {/* 종목/기간을 바꾸면 데이터가 비므로 여기로 들어온다 — 이전 그래프를 남기지 않는다.
                    같은 URL 재조회(새로고침)는 데이터가 남아 있어 화면이 그대로다. */}
                {loading && visible.length === 0 ? (
                    <Box h="full" display="flex" justifyContent="center" alignItems="center">
                        <Spinner size="lg" borderWidth="3px" color="accent.500" />
                    </Box>
                ) : visible.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        {style === "candle" ? (
                            <BarChart data={candleData} margin={CHART_MARGIN} barCategoryGap="18%">
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" opacity={0.1} />
                                <XAxis
                                    dataKey="date"
                                    ticks={visibleTicks.ticks}
                                    tickFormatter={v => visibleTicks.labelMap[v] ?? v}
                                    tickLine={false}
                                    axisLine={false}
                                    tick={AXIS_TICK}
                                    tickMargin={8}
                                    height={28}
                                    interval={0}
                                />
                                <YAxis
                                    domain={candleDomain}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={compactPrice}
                                    width="auto"
                                    tickMargin={Y_TICK_MARGIN}
                                    tick={AXIS_TICK}
                                />
                                <Tooltip
                                    cursor={{ fill: "#94a3b8", opacity: 0.15 }}
                                    content={(p) => (
                                        <CandleTooltip
                                            active={p.active}
                                            payload={p.payload}
                                            label={p.label}
                                            labelFormatter={v => formatOhlcvRangeLabel(String(v), period)}
                                            surface="var(--chakra-colors-bg-panel)"
                                            grid="var(--chakra-colors-border-subtle)"
                                            text="var(--chakra-colors-fg)"
                                        />
                                    )}
                                />
                                <Bar dataKey="_range" shape={<CandleShape />} isAnimationActive={false} />
                            </BarChart>
                        ) : (
                            <AreaChart data={visible} margin={CHART_MARGIN}>
                                <defs>
                                    <linearGradient id={GRAD_ID[period]} x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={color} stopOpacity={0.1} />
                                        <stop offset="95%" stopColor={color} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" opacity={0.1} />
                                <XAxis
                                    dataKey="date"
                                    ticks={visibleTicks.ticks}
                                    tickFormatter={v => visibleTicks.labelMap[v] ?? v}
                                    tickLine={false}
                                    axisLine={false}
                                    tick={AXIS_TICK}
                                    tickMargin={8}
                                    height={28}
                                    interval={0}
                                    padding={{ left: 14, right: 14 }}
                                />
                                <YAxis
                                    domain={yDomain}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={compactPrice}
                                    width="auto"
                                    tickMargin={Y_TICK_MARGIN}
                                    tick={AXIS_TICK}
                                />
                                <Tooltip
                                    contentStyle={TOOLTIP_STYLE}
                                    labelFormatter={v => formatOhlcvRangeLabel(String(v), period)}
                                    formatter={(v: any) => [parseInt(v).toLocaleString(), "종가"]}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="close"
                                    stroke={color}
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill={`url(#${GRAD_ID[period]})`}
                                    dot={false}
                                    isAnimationActive={false}
                                />
                            </AreaChart>
                        )}
                    </ResponsiveContainer>
                ) : (
                    <Box h="full" display="flex" justifyContent="center" alignItems="center">
                        <Text color="fg.subtle" fontSize="sm" fontWeight="medium">
                            {PERIOD_LABELS[period]} 데이터가 없습니다.
                        </Text>
                    </Box>
                )}
            </Box>
        </VStack>
    );
}
