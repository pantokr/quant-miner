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
import { TOOLTIP_STYLE } from "./constants";
import { computeYDomain, formatTimeNum } from "./utils";
import { useFetch } from "./useFetch";

const X_MIN = 90000;
const X_MAX = 153000;
const TIME_TICKS = [90000, 110000, 130000, 153000];
const EMPTY_MINUTE: MinuteChartItem[] = [];

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
    const { data, loading } = useFetch<MinuteChartItem[]>(url, EMPTY_MINUTE);

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

    const clampedTime = Math.min(Math.max(currentTimeNum, X_MIN), X_MAX);
    const numericData = data.map(d => ({ ...d, time_num: parseInt(d.trade_time, 10) }));
    const yDomain = computeYDomain(numericData.map(d => d.close_price));

    return (
        <Box h="300px" w="100%" position="relative">
            {loading && (
                <Box position="absolute" inset={0} display="flex" justifyContent="center" alignItems="center" bg="bg.panel/50" zIndex={1} backdropFilter="blur(2px)">
                    <Spinner color="teal.500" />
                </Box>
            )}
            {numericData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={numericData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
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
                            fontSize={9}
                            fontWeight="bold"
                            tickLine={true}
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
                            labelFormatter={v => formatTimeNum(v as number)}
                            formatter={(v: any) => [parseInt(v).toLocaleString(), "가격"]}
                        />
                        <ReferenceLine
                            x={clampedTime}
                            stroke="#22d3ee"
                            strokeWidth={1.5}
                            strokeDasharray="4 4"
                            label={{
                                value: "현재: " + formatTimeNum(clampedTime),
                                position: "insideBottom",
                                fill: "#22d3ee",
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
