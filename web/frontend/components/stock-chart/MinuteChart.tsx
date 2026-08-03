"use client";

import { useEffect, useMemo, useState } from "react";
import { Box, Spinner, Text } from "@chakra-ui/react";
import {
    Area,
    AreaChart,
    CartesianGrid,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { STOCK_API } from "@/lib/api-config";
import { MinuteChartItem, StockRankItem } from "@/types/stock";
import { AXIS_TICK, CHART_MARGIN, TOOLTIP_STYLE, Y_TICK_MARGIN, compactPrice } from "./constants";
import { computeYDomain, formatTimeNum } from "./utils";
import { useFetch } from "./useFetch";
import { RefreshButton } from "./RefreshButton";

const X_MIN = 90000;
const X_MAX = 153000;
const TIME_TICKS = [90000, 110000, 130000, 153000];
const EMPTY_MINUTE: MinuteChartItem[] = [];

/** 장중에는 스스로 다시 받아온다 — 안 그러면 페이지를 연 시각에서 분봉이 멈춘다 */
const AUTO_REFRESH_MS = 60_000;
const SESSION_FROM = 85000;   // 08:50
const SESSION_TO = 153500;    // 15:35

interface Props {
    stock: StockRankItem;
    color: string;
}

export function MinuteChart({ stock, color }: Props) {
    const today = useMemo(() => {
        const n = new Date();
        return `${n.getFullYear()}${String(n.getMonth() + 1).padStart(2, "0")}${String(n.getDate()).padStart(2, "0")}`;
    }, []);
    const url = `${STOCK_API.MINUTE_CHART(stock.stock_code)}?date=${today}`;

    const [currentTimeNum, setCurrentTimeNum] = useState(() => {
        const n = new Date();
        return n.getHours() * 10000 + n.getMinutes() * 100 + n.getSeconds();
    });

    useEffect(() => {
        const timer = setInterval(() => {
            const n = new Date();
            setCurrentTimeNum(n.getHours() * 10000 + n.getMinutes() * 100 + n.getSeconds());
        }, 30000);
        return () => clearInterval(timer);
    }, []);

    const inSession = currentTimeNum >= SESSION_FROM && currentTimeNum <= SESSION_TO;
    const { data, loading, reload } = useFetch<MinuteChartItem[]>(
        url, EMPTY_MINUTE, inSession ? AUTO_REFRESH_MS : 0,
    );

    const clampedTime = Math.min(Math.max(currentTimeNum, X_MIN), X_MAX);
    const numericData = data.map(d => ({ ...d, time_num: parseInt(d.trade_time, 10) }));
    const yDomain = computeYDomain(numericData.map(d => d.close_price));

    return (
        /* 탭 본문에 주어진 높이를 그대로 채운다 — 세 탭 크기를 맞추기 위함 */
        <Box flex="1" minH={0} w="100%" position="relative">
            <RefreshButton
                onClick={reload}
                busy={loading}
                position="absolute"
                top={0}
                right={0}
                zIndex={2}
            />
            {/* 종목을 바꾸면 데이터가 비므로 여기로 들어온다 — 이전 종목 그래프를 남기지 않는다.
                같은 종목 재조회(새로고침·주기 갱신)는 데이터가 남아 있어 화면이 그대로다. */}
            {loading && numericData.length === 0 ? (
                <Box h="full" display="flex" justifyContent="center" alignItems="center">
                    <Spinner size="lg" borderWidth="3px" color="accent.500" />
                </Box>
            ) : numericData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={numericData} margin={CHART_MARGIN}>
                        <defs>
                            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.1} />
                                <stop offset="95%" stopColor={color} stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" opacity={0.1} />
                        <XAxis
                            dataKey="time_num"
                            type="number"
                            domain={[X_MIN, X_MAX]}
                            ticks={TIME_TICKS}
                            tickFormatter={formatTimeNum}
                            tickLine={true}
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
                            labelFormatter={v => formatTimeNum(v as number)}
                            formatter={(v: any) => [parseInt(v).toLocaleString(), "가격"]}
                        />
                        <ReferenceLine
                            x={clampedTime}
                            stroke="#64748b"
                            strokeWidth={1.5}
                            strokeDasharray="4 4"
                            label={{
                                value: "현재: " + formatTimeNum(clampedTime),
                                position: "insideBottom",
                                fill: "#64748b",
                                fontSize: 9,
                                fontWeight: "bold",
                                offset: 8,
                            }}
                        />
                        <Area
                            type="monotone"
                            dataKey="close_price"
                            stroke={color}
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#colorPrice)"
                            dot={false}
                            isAnimationActive={false}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            ) : (
                <Box h="full" display="flex" justifyContent="center" alignItems="center">
                    <Text color="fg.subtle" fontSize="sm" fontWeight="medium">
                        데이터를 불러오는 중이거나 장외 시간입니다.
                    </Text>
                </Box>
            )}
        </Box>
    );
}
