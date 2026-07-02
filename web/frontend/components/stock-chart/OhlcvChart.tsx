"use client";

import { useEffect, useRef, useState } from "react";
import { Box, HStack, Spinner, Text, VStack } from "@chakra-ui/react";
import {
    Area,
    AreaChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { STOCK_API } from "@/lib/api-config";
import { OHLCVItem, StockRankItem } from "@/types/stock";
import {
    FIXED_WINDOW,
    GRAD_ID,
    MAX_TICKS,
    OhlcvPeriod,
    PAN_STEP,
    PERIOD_LABELS,
    TOOLTIP_STYLE,
} from "./constants";
import {
    computeOhlcvTicks,
    computeYDomain,
    formatOhlcvDate,
    formatOhlcvRangeLabel,
} from "./utils";
import { useFetch } from "./useFetch";

const EMPTY_OHLCV: OHLCVItem[] = [];

interface Props {
    stock: StockRankItem;
    period: OhlcvPeriod;
    color: string;
}

export function OhlcvChart({ stock, period, color }: Props) {
    const periodSuffix = period === "daily" ? "" : period === "monthly" ? "?period=M" : "?period=Y";
    const url = `${STOCK_API.OHLCV_ALL(stock.stock_code)}${periodSuffix}`;
    const { data, loading } = useFetch<OHLCVItem[]>(url, EMPTY_OHLCV);

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

    const rangeLabel = visible.length >= 2
        ? `${formatOhlcvRangeLabel(visible[0].date, period)} ~ ${formatOhlcvRangeLabel(visible[visible.length - 1].date, period)}`
        : "";

    const widthLabel = period === "daily" ? `${winSize}일` : period === "monthly" ? `${winSize}개월` : `${winSize}년`;

    return (
        <VStack align="stretch" gap={2}>
            <VStack align="stretch" gap={2} px={1}>
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
                </HStack>
                <Text fontSize="2xs" color="fg.muted" textAlign="center" fontWeight="medium">
                    💡 차트를 드래그하거나 마우스 휠로 기간을 이동하세요 ({widthLabel} 표시)
                </Text>
            </VStack>

            <Box
                ref={containerRef}
                h="300px"
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
                {loading && (
                    <Box position="absolute" inset={0} display="flex" justifyContent="center" alignItems="center" bg="bg.panel/50" zIndex={1} backdropFilter="blur(2px)">
                        <Spinner color="teal.500" />
                    </Box>
                )}
                {visible.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={visible} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
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
                                fontSize={9}
                                fontWeight="bold"
                                tickLine={false}
                                axisLine={false}
                                tick={{ fill: "#94a3b8" }}
                                interval={0}
                            />
                            <YAxis
                                domain={yDomain}
                                fontSize={9}
                                fontWeight="bold"
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={v => v.toLocaleString()}
                                width={56}
                                tick={{ fill: "#94a3b8" }}
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
