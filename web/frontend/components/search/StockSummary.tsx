"use client";

import { Badge, Box, HStack, SimpleGrid, Spinner, Text, VStack } from "@chakra-ui/react";
import { STOCK_API } from "@/lib/api-config";
import { CurrentPriceResponse } from "@/types/stock";
import { useFetch } from "@/components/stock-chart/useFetch";
import { SelectedStock } from "./SearchBox";

interface Props {
    stock: SelectedStock;
}

function Metric({ label, value, color }: { label: string; value: string; color?: string }) {
    return (
        <VStack align="start" gap={1}>
            <Text fontSize="2xs" fontWeight="black" color="fg.muted" letterSpacing="wider">
                {label}
            </Text>
            <Text fontSize="lg" fontWeight="900" color={color ?? "fg"} fontVariantNumeric="tabular-nums">
                {value}
            </Text>
        </VStack>
    );
}

export function StockSummary({ stock }: Props) {
    const { data, loading } = useFetch<CurrentPriceResponse | null>(
        STOCK_API.CURRENT(stock.code),
        null,
    );

    const isUp = (data?.change_rate ?? 0) >= 0;
    const moveColor = isUp ? "red.500" : "blue.500";
    const num = (v: number | undefined) => (v === undefined ? "-" : v.toLocaleString());

    return (
        <Box
            bg="bg.panel"
            borderRadius="2xl"
            borderWidth="1px"
            borderColor="border.subtle"
            p={6}
            boxShadow="xs"
            position="relative"
        >
            {loading && (
                <Box position="absolute" top={4} right={4}>
                    <Spinner size="sm" color="accent.500" />
                </Box>
            )}

            <HStack justify="space-between" align="start" flexWrap="wrap" gap={4} mb={6}>
                <VStack align="start" gap={1}>
                    <HStack gap={2}>
                        <Text fontSize="2xl" fontWeight="900" color="fg" letterSpacing="tight">
                            {stock.name}
                        </Text>
                        <Badge size="sm" variant="subtle" colorPalette="gray" borderRadius="md">
                            {stock.code}
                        </Badge>
                        {stock.market && (
                            <Badge
                                size="sm"
                                variant="subtle"
                                colorPalette={stock.market === "KOSPI" ? "blue" : "purple"}
                                borderRadius="md"
                            >
                                {stock.market}
                            </Badge>
                        )}
                    </HStack>
                    <Text fontSize="xs" fontWeight="medium" color="fg.subtle">
                        현재가는 KIS 실시간 조회, 나머지 표는 DB 우선 · 미보유 시 수집 후 적재
                    </Text>
                </VStack>

                <VStack align="end" gap={0}>
                    <Text fontSize="3xl" fontWeight="900" color="fg" lineHeight="1" fontVariantNumeric="tabular-nums">
                        {data ? data.current.toLocaleString() : "—"}
                    </Text>
                    {data && (
                        <Text fontSize="sm" fontWeight="bold" color={moveColor} mt={1}>
                            {isUp ? "+" : ""}{data.change_val.toLocaleString()} ({isUp ? "+" : ""}{data.change_rate}%)
                        </Text>
                    )}
                </VStack>
            </HStack>

            <SimpleGrid columns={{ base: 2, md: 4, xl: 8 }} gap={5}>
                <Metric label="시가" value={num(data?.open)} />
                <Metric label="고가" value={num(data?.high)} color={data ? "red.500" : undefined} />
                <Metric label="저가" value={num(data?.low)} color={data ? "blue.500" : undefined} />
                <Metric label="거래량" value={num(data?.volume)} />
                <Metric label="시가총액(억)" value={num(data?.market_cap)} />
                <Metric label="PER" value={data ? String(data.per) : "-"} />
                <Metric label="PBR" value={data ? String(data.pbr) : "-"} />
                <Metric label="외국인비율" value={data ? `${data.foreign_ratio}%` : "-"} />
            </SimpleGrid>
        </Box>
    );
}
