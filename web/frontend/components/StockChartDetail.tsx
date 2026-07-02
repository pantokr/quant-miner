"use client";

import { useState } from "react";
import { Badge, Box, HStack, Icon, Tabs, Text, VStack } from "@chakra-ui/react";
import { List, TrendingUp, Users } from "lucide-react";
import { StockRankItem } from "@/types/stock";
import { ChartPeriod, PERIOD_LABELS } from "./stock-chart/constants";
import { MinuteChart } from "./stock-chart/MinuteChart";
import { OhlcvChart } from "./stock-chart/OhlcvChart";
import { OrderbookTab } from "./stock-chart/OrderbookTab";
import { InvestorTab } from "./stock-chart/InvestorTab";

interface StockChartDetailProps {
    stock: StockRankItem | null;
}

export function StockChartDetail({ stock }: StockChartDetailProps) {
    const [chartPeriod, setChartPeriod] = useState<ChartPeriod>("minute");

    if (!stock) {
        return (
            <Box bg="bg.panel" borderRadius="2xl" borderWidth="1px" borderColor="border.subtle" p={20} textAlign="center" boxShadow="xs">
                <VStack gap={4}>
                    <Icon as={TrendingUp} boxSize="10" color="fg.muted" opacity={0.3} />
                    <Text color="fg.subtle" fontWeight="medium">종목을 선택하여 상세 정보를 확인하세요.</Text>
                </VStack>
            </Box>
        );
    }

    const isUp = stock.change_rate >= 0;
    const color = isUp ? "#ef4444" : "#3b82f6";

    return (
        <Box bg="bg.panel" borderRadius="2xl" borderWidth="1px" borderColor="border.subtle" p={6} h="100%" boxShadow="xs">
            <VStack align="stretch" gap={6}>
                {/* 헤더 */}
                <HStack justify="space-between" align="start">
                    <VStack align="start" gap={1}>
                        <HStack gap={2}>
                            <Text fontSize="2xl" fontWeight="900" color="fg" letterSpacing="tight">
                                {stock.stock_name}
                            </Text>
                            <Badge size="sm" variant="subtle" colorPalette="gray" borderRadius="md">
                                {stock.stock_code}
                            </Badge>
                        </HStack>
                        <Text fontSize="xs" fontWeight="bold" color="fg.muted" letterSpacing="widest">
                            KOSPI MARKET
                        </Text>
                    </VStack>
                    <VStack align="end" gap={0}>
                        <Text fontSize="3xl" fontWeight="900" color="fg" lineHeight="1">
                            {stock.price.toLocaleString()}
                        </Text>
                        <HStack gap={1} mt={1}>
                            <Text fontSize="sm" fontWeight="bold" color={isUp ? "red.500" : "blue.500"}>
                                {isUp ? "+" : ""}{stock.change_rate}%
                            </Text>
                        </HStack>
                    </VStack>
                </HStack>

                <Tabs.Root defaultValue="chart" variant="enclosed">
                    {/* 탭 헤더 + 기간 스위치 */}
                    <HStack justify="space-between" align="center" mb={2}>
                        <Tabs.List bg="bg.muted" p={1} borderRadius="xl" border="none" w="fit-content">
                            <Tabs.Trigger value="chart" borderRadius="lg" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "teal.500" }} fontSize="xs" fontWeight="bold" px={3} gap={1}>
                                <Icon as={TrendingUp} boxSize="3" />차트
                            </Tabs.Trigger>
                            <Tabs.Trigger value="orderbook" borderRadius="lg" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "teal.500" }} fontSize="xs" fontWeight="bold" px={3} gap={1}>
                                <Icon as={List} boxSize="3" />호가
                            </Tabs.Trigger>
                            <Tabs.Trigger value="investor" borderRadius="lg" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "teal.500" }} fontSize="xs" fontWeight="bold" px={3} gap={1}>
                                <Icon as={Users} boxSize="3" />투자자
                            </Tabs.Trigger>
                        </Tabs.List>

                        <HStack gap={1}>
                            {(["minute", "daily", "monthly", "yearly"] as const).map(p => (
                                <Box
                                    key={p}
                                    as="button"
                                    px={2.5} py={1}
                                    borderRadius="md"
                                    fontSize="xs"
                                    fontWeight="bold"
                                    cursor="pointer"
                                    bg={chartPeriod === p ? "teal.500" : "bg.muted"}
                                    color={chartPeriod === p ? "white" : "fg.muted"}
                                    onClick={() => setChartPeriod(p)}
                                    transition="all 0.15s"
                                >
                                    {PERIOD_LABELS[p]}
                                </Box>
                            ))}
                        </HStack>
                    </HStack>

                    <Tabs.Content value="chart" pt={2}>
                        {chartPeriod === "minute" ? (
                            <MinuteChart stock={stock} color={color} />
                        ) : (
                            <OhlcvChart stock={stock} period={chartPeriod} color={color} />
                        )}
                    </Tabs.Content>

                    <Tabs.Content value="orderbook" pt={4}>
                        <OrderbookTab stock={stock} />
                    </Tabs.Content>

                    <Tabs.Content value="investor" pt={4}>
                        <InvestorTab stock={stock} />
                    </Tabs.Content>
                </Tabs.Root>
            </VStack>
        </Box>
    );
}
