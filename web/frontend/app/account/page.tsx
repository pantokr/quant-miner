"use client";

import { Box, VStack, HStack, Heading, Text, SimpleGrid, Table, Spinner, Tabs, Icon } from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { ACCOUNT_API } from "@/lib/api-config";
import { fetchJson } from "@/lib/api-error";
import {
    TABLE_CELL,
    TABLE_HEADER_CELL,
    TABLE_HEADER_ROW,
    TABLE_NUM_CELL,
    TABLE_ROW,
    TABLE_SURFACE,
} from "@/lib/table-style";
import { PortfolioBreakdown } from "@/components/account/PortfolioBreakdown";
import { AccountBalanceResponse, OrderExecution } from "@/types/stock";
import { AlertTriangle, Inbox, Wallet, PieChart, TrendingUp } from "lucide-react";

const message = (e: unknown) => (e instanceof Error ? e.message : String(e));

/** 빈 표에 이유를 남긴다 — 값이 없는 것과 못 불러온 것은 다른 상황이다 */
function EmptyRow({ message }: { message: string }) {
    return (
        <VStack gap={3}>
            <Icon as={Inbox} boxSize="7" color="fg.muted" opacity={0.3} />
            <Text fontSize="sm" color="fg.subtle" fontWeight="medium" textAlign="center">
                {message}
            </Text>
        </VStack>
    );
}

export default function AccountPage() {
    const [balance, setBalance] = useState<AccountBalanceResponse | null>(null);
    const [orders, setOrders] = useState<OrderExecution[]>([]);
    const [loading, setLoading] = useState(true);
    // 잔고와 주문체결은 따로 실패할 수 있다 (KIS 모의투자는 체결 조회를 막는 경우가 있다).
    // 한쪽이 죽었다고 다른 쪽까지 안 보이면 원인을 짚을 수 없어 오류를 나눠 담는다.
    const [balanceError, setBalanceError] = useState("");
    const [ordersError, setOrdersError] = useState("");

    useEffect(() => {
        let cancelled = false;

        const load = async () => {
            const [balanceRes, ordersRes] = await Promise.allSettled([
                fetchJson<AccountBalanceResponse>(ACCOUNT_API.BALANCE),
                fetchJson<OrderExecution[]>(ACCOUNT_API.DAILY_CCLD),
            ]);
            if (cancelled) return;

            if (balanceRes.status === "fulfilled") {
                setBalance(balanceRes.value);
                setBalanceError("");
            } else {
                setBalance(null);
                setBalanceError(message(balanceRes.reason));
            }

            if (ordersRes.status === "fulfilled") {
                setOrders(ordersRes.value ?? []);
                setOrdersError("");
            } else {
                setOrders([]);
                setOrdersError(message(ordersRes.reason));
            }

            setLoading(false);
        };

        load();
        return () => { cancelled = true; };
    }, []);

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" h="100vh" bg="bg.main">
                <Spinner size="xl" color="accent.500" />
            </Box>
        );
    }

    return (
        <Box p={{ base: 6, lg: 10 }} bg="bg.main" minH="100%">
            <VStack align="start" mb={10} gap={2}>
                <Heading size="2xl" fontWeight="900" color="fg" letterSpacing="tight">나의 계좌</Heading>
                <Text fontSize="md" fontWeight="medium" color="fg.subtle">실시간 자산 포트폴리오 및 주문 체결 내역</Text>
            </VStack>

            {/* 조용히 비는 화면이 제일 나쁘다 — 왜 안 보이는지 여기서 말해 준다 */}
            {balanceError && (
                <HStack
                    gap={3}
                    align="start"
                    bg="red.500/10"
                    borderWidth="1px"
                    borderColor="red.500/30"
                    borderRadius="xl"
                    px={5} py={4}
                    mb={10}
                >
                    <Icon as={AlertTriangle} boxSize="4" color="red.500" flexShrink={0} mt={0.5} />
                    <VStack align="start" gap={0.5}>
                        <Text fontSize="sm" fontWeight="bold" color="fg">잔고를 불러오지 못했습니다</Text>
                        <Text fontSize="xs" fontWeight="medium" color="fg.subtle">{balanceError}</Text>
                    </VStack>
                </HStack>
            )}

            {balance && (
                <SimpleGrid columns={{ base: 1, md: 3 }} gap={6} mb={10}>
                    <Box bg="bg.panel" p={8} borderRadius="2xl" border="1px solid" borderColor="border.subtle" boxShadow="xs" position="relative" overflow="hidden">
                        <Box position="absolute" top={-2} right={-2} opacity={0.05}>
                            <Icon as={Wallet} boxSize="24" color="accent.500" />
                        </Box>
                        <Text fontSize="xs" fontWeight="black" color="fg.muted" mb={4} letterSpacing="widest">DEPOSIT</Text>
                        <Text fontSize="3xl" fontWeight="900" color="fg">₩{balance.summary.deposit.toLocaleString()}</Text>
                    </Box>
                    <Box bg="bg.panel" p={8} borderRadius="2xl" border="1px solid" borderColor="border.subtle" boxShadow="xs" position="relative" overflow="hidden">
                        <Box position="absolute" top={-2} right={-2} opacity={0.05}>
                            <Icon as={PieChart} boxSize="24" color="accent.500" />
                        </Box>
                        <Text fontSize="xs" fontWeight="black" color="fg.muted" mb={4} letterSpacing="widest">TOTAL EVALUATION</Text>
                        <Text fontSize="3xl" fontWeight="900" color="fg">₩{balance.summary.total_eval.toLocaleString()}</Text>
                    </Box>
                    <Box bg="bg.panel" p={8} borderRadius="2xl" border="1px solid" borderColor="border.subtle" boxShadow="xs" position="relative" overflow="hidden">
                        <Box position="absolute" top={-2} right={-2} opacity={0.05}>
                            <Icon as={TrendingUp} boxSize="24" color="accent.500" />
                        </Box>
                        <Text fontSize="xs" fontWeight="black" color="fg.muted" mb={4} letterSpacing="widest">PROFIT / LOSS</Text>
                        <Text fontSize="3xl" fontWeight="900" color={balance.summary.total_profit >= 0 ? "red.600" : "blue.600"}>
                            ₩{balance.summary.total_profit.toLocaleString()}
                        </Text>
                    </Box>
                </SimpleGrid>
            )}

            {/* 요약 숫자만으로는 "어디에 얼마나 실려 있는지"가 안 보인다 — 비중을 먼저 보여 준다 */}
            {balance && (
                <Box mb={10}>
                    <PortfolioBreakdown summary={balance.summary} stocks={balance.stocks} />
                </Box>
            )}

            <Tabs.Root defaultValue="stocks" variant="enclosed">
                <Tabs.List bg="bg.muted" p={1} borderRadius="2xl" mb={6} border="none" w="fit-content">
                    <Tabs.Trigger value="stocks" borderRadius="xl" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "accent.600" }} fontSize="sm" fontWeight="bold" px={8} py={2}>
                        보유 종목
                    </Tabs.Trigger>
                    <Tabs.Trigger value="orders" borderRadius="xl" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "accent.600" }} fontSize="sm" fontWeight="bold" px={8} py={2}>
                        주문 체결
                    </Tabs.Trigger>
                </Tabs.List>

                <Tabs.Content value="stocks">
                    <Box {...TABLE_SURFACE}>
                        <Table.Root size="md" variant="line">
                            <Table.Header>
                                <Table.Row {...TABLE_HEADER_ROW}>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL}>STOCK</Table.ColumnHeader>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right">QUANTITY</Table.ColumnHeader>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right">AVG PRICE</Table.ColumnHeader>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right">CURRENT</Table.ColumnHeader>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right">PROFIT</Table.ColumnHeader>
                                </Table.Row>
                            </Table.Header>
                            <Table.Body>
                                {balance?.stocks.map((stock) => (
                                    <Table.Row key={stock.stock_code} {...TABLE_ROW}>
                                        <Table.Cell {...TABLE_CELL} py={3}>
                                            <VStack align="start" gap={0}>
                                                <Text fontWeight="semibold" fontSize="sm" color="fg">{stock.stock_name}</Text>
                                                <Text fontSize="2xs" color="fg.muted" fontFamily="mono">{stock.stock_code}</Text>
                                            </VStack>
                                        </Table.Cell>
                                        <Table.Cell {...TABLE_NUM_CELL} py={3}>{stock.quantity.toLocaleString()}</Table.Cell>
                                        <Table.Cell {...TABLE_NUM_CELL} py={3} color="fg.subtle">₩{stock.avg_price.toLocaleString()}</Table.Cell>
                                        <Table.Cell {...TABLE_NUM_CELL} py={3}>₩{stock.current_price.toLocaleString()}</Table.Cell>
                                        {/* 손익은 배지 대신 색 글자로 — 행마다 알약이 박히면 표가 시끄럽다 */}
                                        <Table.Cell
                                            {...TABLE_NUM_CELL}
                                            py={3}
                                            fontWeight="semibold"
                                            color={stock.profit_rate >= 0 ? "red.500" : "blue.500"}
                                        >
                                            {stock.profit_rate >= 0 ? "+" : ""}{stock.profit_rate}%
                                        </Table.Cell>
                                    </Table.Row>
                                ))}
                                {!balance?.stocks.length && (
                                    <Table.Row>
                                        <Table.Cell colSpan={5} py={14}>
                                            <EmptyRow
                                                message={balanceError
                                                    ? "잔고를 불러오지 못해 보유 종목을 표시할 수 없습니다."
                                                    : "보유 중인 종목이 없습니다."}
                                            />
                                        </Table.Cell>
                                    </Table.Row>
                                )}
                            </Table.Body>
                        </Table.Root>
                    </Box>
                </Tabs.Content>

                <Tabs.Content value="orders">
                    <Box {...TABLE_SURFACE}>
                        <Table.Root size="md" variant="line">
                            <Table.Header>
                                <Table.Row {...TABLE_HEADER_ROW}>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL}>ORDER NO</Table.ColumnHeader>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL}>STOCK</Table.ColumnHeader>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL}>SIDE</Table.ColumnHeader>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right">ORDER QTY</Table.ColumnHeader>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right">FILLED</Table.ColumnHeader>
                                    <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right">PRICE</Table.ColumnHeader>
                                </Table.Row>
                            </Table.Header>
                            <Table.Body>
                                {orders.map((order) => (
                                    <Table.Row key={order.order_no} {...TABLE_ROW}>
                                        <Table.Cell {...TABLE_CELL} py={3} fontSize="2xs" color="fg.muted" fontFamily="mono">
                                            {order.order_no}
                                        </Table.Cell>
                                        <Table.Cell {...TABLE_CELL} py={3}>
                                            <VStack align="start" gap={0}>
                                                <Text fontWeight="semibold" fontSize="sm" color="fg">{order.stock_name}</Text>
                                                <Text fontSize="2xs" color="fg.muted" fontFamily="mono">{order.stock_code}</Text>
                                            </VStack>
                                        </Table.Cell>
                                        {/* 매수/매도는 색 글자로 — 채운 배지는 표에서 가장 먼저 눈에 띄는데 정작 값이 아니다 */}
                                        <Table.Cell
                                            {...TABLE_CELL}
                                            py={3}
                                            fontWeight="semibold"
                                            color={order.side === "매수" ? "red.500" : "blue.500"}
                                        >
                                            {order.side}
                                        </Table.Cell>
                                        <Table.Cell {...TABLE_NUM_CELL} py={3}>{order.order_qty.toLocaleString()}</Table.Cell>
                                        <Table.Cell {...TABLE_NUM_CELL} py={3} color="accent.600">{order.filled_qty.toLocaleString()}</Table.Cell>
                                        <Table.Cell {...TABLE_NUM_CELL} py={3} fontWeight="semibold">₩{order.avg_price.toLocaleString()}</Table.Cell>
                                    </Table.Row>
                                ))}
                                {!orders.length && (
                                    <Table.Row>
                                        <Table.Cell colSpan={6} py={14}>
                                            <EmptyRow
                                                message={ordersError || "오늘 체결된 주문이 없습니다."}
                                            />
                                        </Table.Cell>
                                    </Table.Row>
                                )}
                            </Table.Body>
                        </Table.Root>
                    </Box>
                </Tabs.Content>
            </Tabs.Root>
        </Box>
    );
}
