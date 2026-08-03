"use client";

import { useMemo, useState } from "react";
import { Box, HStack, Text, VStack } from "@chakra-ui/react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { useDarkMode } from "@/hooks/useDarkMode";
import { CHROME_DARK, CHROME_LIGHT, seriesColor } from "@/lib/viz-palette";
import { AccountSummary, HoldingStock } from "@/types/stock";

/**
 * 조각이 이보다 많아지면 인접한 색이 붙어 서로 구분되지 않는다.
 * 넘치는 종목은 "기타"로 접고, 정확한 값은 옆 목록과 아래 보유 종목 표가 나른다.
 */
const MAX_SLICES = 6;

interface Props {
    summary: AccountSummary;
    stocks: HoldingStock[];
}

interface Slice {
    name: string;
    value: number;
    /** 팔레트 슬롯 — 종목이 걸러져도 색이 따라 움직이지 않도록 만들 때 한 번만 정한다 */
    color: string;
    /** 평가손익률 (예수금·기타에는 없다) */
    rate?: number;
}

const won = (v: number) => `₩${Math.round(v).toLocaleString("ko-KR")}`;

export function PortfolioBreakdown({ summary, stocks }: Props) {
    const dark = useDarkMode();
    const chrome = dark ? CHROME_DARK : CHROME_LIGHT;
    // 기본은 예수금 포함 — "내 돈이 어디에 얼마나 있나"는 현금까지 세어야 답이 된다.
    // 종목끼리의 비중만 보고 싶을 때 끄면 된다.
    const [withCash, setWithCash] = useState(true);

    const { slices, total, stockTotal } = useMemo(() => {
        // 평가금액 = 현재가 × 수량. KIS 요약의 total_eval은 계좌 구성에 따라 예수금 포함
        // 여부가 갈려서, 비중 계산에는 보유 종목에서 직접 더한 값을 쓴다.
        const valued = stocks
            .map(s => ({
                name: s.stock_name,
                value: s.current_price * s.quantity,
                rate: s.profit_rate,
            }))
            .filter(s => s.value > 0)
            .sort((a, b) => b.value - a.value);

        const stockSum = valued.reduce((sum, s) => sum + s.value, 0);
        const cash = withCash ? Math.max(0, summary.deposit) : 0;

        // 예수금이 한 자리를 차지하므로 종목 몫이 하나 줄어든다
        const room = MAX_SLICES - (cash > 0 ? 1 : 0);
        const head = valued.slice(0, room);
        const tail = valued.slice(room);

        const out: Slice[] = head.map((s, i) => ({ ...s, color: seriesColor(i, dark) }));

        if (tail.length) {
            out.push({
                name: `기타 ${tail.length}종목`,
                value: tail.reduce((sum, s) => sum + s.value, 0),
                color: chrome.axis,
            });
        }
        if (cash > 0) {
            // 예수금은 투자하지 않은 몫이라 시리즈 색을 주지 않는다 — 회색이 그 뜻이다
            out.push({ name: "예수금", value: cash, color: chrome.muted });
        }

        return { slices: out, total: stockSum + cash, stockTotal: stockSum };
    }, [stocks, summary.deposit, withCash, dark, chrome.axis, chrome.muted]);

    if (!slices.length) {
        return (
            <Box bg="bg.panel" borderRadius="xl" borderWidth="1px" borderColor="border.subtle" p={10}>
                <Text fontSize="sm" color="fg.subtle" fontWeight="medium" textAlign="center">
                    {withCash
                        ? "보유 종목도 예수금도 없습니다."
                        : "보유 중인 종목이 없습니다. ‘예수금 포함’을 켜면 현금 비중을 볼 수 있습니다."}
                </Text>
            </Box>
        );
    }

    const share = (v: number) => (total > 0 ? (v / total) * 100 : 0);
    const topShare = share(slices[0].value);

    return (
        <Box bg="bg.panel" borderRadius="xl" borderWidth="1px" borderColor="border.subtle" p={6}>
            <HStack justify="space-between" align="start" mb={5} flexWrap="wrap" gap={3}>
                <VStack align="start" gap={0.5}>
                    <Text fontSize="sm" fontWeight="bold" color="fg">투자 비중</Text>
                    <Text fontSize="xs" color="fg.subtle" fontWeight="medium">
                        {withCash
                            ? "평가금액(현재가 × 수량) + 예수금 기준"
                            : "평가금액(현재가 × 수량) 기준"}
                    </Text>
                </VStack>
                <Box
                    as="button"
                    px={3} py={1.5}
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor={withCash ? "accent.500" : "border.subtle"}
                    bg={withCash ? "accent.500" : "bg.panel"}
                    color={withCash ? "white" : "fg.subtle"}
                    fontSize="xs"
                    fontWeight="bold"
                    cursor="pointer"
                    transition="all 0.15s"
                    onClick={() => setWithCash(v => !v)}
                >
                    예수금 포함
                </Box>
            </HStack>

            <HStack align="center" gap={8} flexWrap="wrap">
                {/* 도넛 — 가운데 구멍에 합계를 놓아 조각이 무엇의 몫인지 바로 읽힌다 */}
                <Box position="relative" w="220px" h="220px" flexShrink={0}>
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={slices}
                                dataKey="value"
                                nameKey="name"
                                innerRadius="62%"
                                outerRadius="100%"
                                startAngle={90}
                                endAngle={-270}
                                // 조각 사이를 판 색으로 2px 띄운다 — 테두리를 그리는 것보다 조용하다
                                stroke={chrome.surface}
                                strokeWidth={2}
                                isAnimationActive={false}
                            >
                                {slices.map(s => <Cell key={s.name} fill={s.color} />)}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    borderRadius: 10,
                                    border: `1px solid ${chrome.grid}`,
                                    background: chrome.surface,
                                    color: chrome.text,
                                    fontSize: 12,
                                    fontWeight: 600,
                                }}
                                formatter={(v, name) => [
                                    `${won(Number(v))} · ${share(Number(v)).toFixed(1)}%`,
                                    String(name ?? ""),
                                ]}
                            />
                        </PieChart>
                    </ResponsiveContainer>

                    <VStack
                        position="absolute"
                        inset={0}
                        justify="center"
                        gap={0}
                        pointerEvents="none"
                    >
                        <Text fontSize="2xs" fontWeight="bold" color="fg.muted" letterSpacing="wider">
                            {withCash ? "총 자산" : "주식 평가금액"}
                        </Text>
                        <Text fontSize="lg" fontWeight="bold" color="fg" lineHeight="1.2">
                            {won(total)}
                        </Text>
                    </VStack>
                </Box>

                {/* 범례 겸 값 목록 — 색만으로 정체를 싣지 않고, 정확한 수치도 여기서 읽는다 */}
                <VStack align="stretch" gap={2} flex="1" minW="260px">
                    {slices.map(s => (
                        <HStack key={s.name} gap={3}>
                            <Box w="8px" h="8px" borderRadius="full" bg={s.color} flexShrink={0} />
                            <Text fontSize="xs" fontWeight="medium" color="fg" flex="1" truncate>
                                {s.name}
                            </Text>
                            {s.rate !== undefined && (
                                <Text
                                    fontSize="2xs"
                                    fontWeight="semibold"
                                    fontFamily="mono"
                                    color={s.rate >= 0 ? "red.500" : "blue.500"}
                                    minW="56px"
                                    textAlign="right"
                                >
                                    {s.rate >= 0 ? "+" : ""}{s.rate}%
                                </Text>
                            )}
                            <Text
                                fontSize="xs"
                                color="fg.subtle"
                                fontFamily="mono"
                                fontVariantNumeric="tabular-nums"
                                minW="110px"
                                textAlign="right"
                            >
                                {won(s.value)}
                            </Text>
                            <Text
                                fontSize="xs"
                                fontWeight="semibold"
                                color="fg"
                                fontFamily="mono"
                                fontVariantNumeric="tabular-nums"
                                minW="52px"
                                textAlign="right"
                            >
                                {share(s.value).toFixed(1)}%
                            </Text>
                        </HStack>
                    ))}

                    {/* 쏠림은 표를 읽어야 알 수 있는 값이라 한 줄로 미리 말해 준다 */}
                    <Text fontSize="2xs" color="fg.muted" fontWeight="medium" pt={1}>
                        가장 큰 비중은 {slices[0].name} {topShare.toFixed(1)}%
                        {withCash && stockTotal > 0 && ` · 주식 ${share(stockTotal).toFixed(1)}%`}
                    </Text>
                </VStack>
            </HStack>
        </Box>
    );
}
