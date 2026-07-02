"use client";

import { Box, VStack, Heading, Text, SimpleGrid, Table, Badge, Spinner, Tabs, Icon, HStack } from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { ACCOUNT_API } from "@/lib/api-config";
import { AccountBalanceResponse, OrderExecution } from "@/types/stock";
import { Wallet, PieChart, TrendingUp } from "lucide-react";

export default function AccountPage() {
    const [balance, setBalance] = useState<AccountBalanceResponse | null>(null);
    const [orders, setOrders] = useState<OrderExecution[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAccountData = async () => {
            setLoading(true);
            try {
                const [balanceRes, ordersRes] = await Promise.all([
                    fetch(ACCOUNT_API.BALANCE),
                    fetch(ACCOUNT_API.DAILY_CCLD)
                ]);

                if (balanceRes.ok) setBalance(await balanceRes.json());
                if (ordersRes.ok) setOrders(await ordersRes.json());
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchAccountData();
    }, []);

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" h="100vh" bg="bg.main">
                <Spinner size="xl" color="teal.500" />
            </Box>
        );
    }

    return (
        <Box p={{ base: 6, lg: 10 }} bg="bg.main" minH="100vh">
            <VStack align="start" mb={10} gap={2}>
                <Heading size="2xl" fontWeight="900" color="fg" letterSpacing="tight">나의 계좌</Heading>
                <Text fontSize="md" fontWeight="medium" color="fg.subtle">실시간 자산 포트폴리오 및 주문 체결 내역</Text>
            </VStack>

            {balance && (
                <SimpleGrid columns={{ base: 1, md: 3 }} gap={6} mb={10}>
                    <Box bg="bg.panel" p={8} borderRadius="2xl" border="1px solid" borderColor="border.subtle" boxShadow="xs" position="relative" overflow="hidden">
                        <Box position="absolute" top={-2} right={-2} opacity={0.05}>
                            <Icon as={Wallet} boxSize="24" color="teal.500" />
                        </Box>
                        <Text fontSize="xs" fontWeight="black" color="fg.muted" mb={4} letterSpacing="widest">DEPOSIT</Text>
                        <Text fontSize="3xl" fontWeight="900" color="fg">₩{balance.summary.deposit.toLocaleString()}</Text>
                    </Box>
                    <Box bg="bg.panel" p={8} borderRadius="2xl" border="1px solid" borderColor="border.subtle" boxShadow="xs" position="relative" overflow="hidden">
                        <Box position="absolute" top={-2} right={-2} opacity={0.05}>
                            <Icon as={PieChart} boxSize="24" color="teal.500" />
                        </Box>
                        <Text fontSize="xs" fontWeight="black" color="fg.muted" mb={4} letterSpacing="widest">TOTAL EVALUATION</Text>
                        <Text fontSize="3xl" fontWeight="900" color="fg">₩{balance.summary.total_eval.toLocaleString()}</Text>
                    </Box>
                    <Box bg="bg.panel" p={8} borderRadius="2xl" border="1px solid" borderColor="border.subtle" boxShadow="xs" position="relative" overflow="hidden">
                        <Box position="absolute" top={-2} right={-2} opacity={0.05}>
                            <Icon as={TrendingUp} boxSize="24" color="teal.500" />
                        </Box>
                        <Text fontSize="xs" fontWeight="black" color="fg.muted" mb={4} letterSpacing="widest">PROFIT / LOSS</Text>
                        <Text fontSize="3xl" fontWeight="900" color={balance.summary.total_profit >= 0 ? "red.600" : "blue.600"}>
                            ₩{balance.summary.total_profit.toLocaleString()}
                        </Text>
                    </Box>
                </SimpleGrid>
            )}

            <Tabs.Root defaultValue="stocks" variant="enclosed">
                <Tabs.List bg="bg.muted" p={1} borderRadius="2xl" mb={6} border="none" w="fit-content">
                    <Tabs.Trigger value="stocks" borderRadius="xl" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "teal.600" }} fontSize="sm" fontWeight="bold" px={8} py={2}>
                        보유 종목
                    </Tabs.Trigger>
                    <Tabs.Trigger value="orders" borderRadius="xl" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "teal.600" }} fontSize="sm" fontWeight="bold" px={8} py={2}>
                        주문 체결
                    </Tabs.Trigger>
                </Tabs.List>

                <Tabs.Content value="stocks">
                    <Box bg="bg.panel" borderRadius="2xl" border="1px solid" borderColor="border.subtle" overflow="hidden" boxShadow="xs">
                        <Table.Root size="md" variant="line">
                            <Table.Header>
                                <Table.Row bg="bg.muted">
                                    <Table.ColumnHeader color="fg.muted" fontSize="xs" fontWeight="black">STOCK</Table.ColumnHeader>
                                    <Table.ColumnHeader textAlign="right" color="fg.muted" fontSize="xs" fontWeight="black">QUANTITY</Table.ColumnHeader>
                                    <Table.ColumnHeader textAlign="right" color="fg.muted" fontSize="xs" fontWeight="black">AVG PRICE</Table.ColumnHeader>
                                    <Table.ColumnHeader textAlign="right" color="fg.muted" fontSize="xs" fontWeight="black">CURRENT</Table.ColumnHeader>
                                    <Table.ColumnHeader textAlign="right" color="fg.muted" fontSize="xs" fontWeight="black">PROFIT</Table.ColumnHeader>
                                </Table.Row>
                            </Table.Header>
                            <Table.Body>
                                {balance?.stocks.map((stock) => (
                                    <Table.Row key={stock.stock_code} _hover={{ bg: "bg.muted" }}>
                                        <Table.Cell>
                                            <VStack align="start" gap={0}>
                                                <Text fontWeight="800" color="fg">{stock.stock_name}</Text>
                                                <Text fontSize="2xs" fontWeight="bold" color="fg.muted">{stock.stock_code}</Text>
                                            </VStack>
                                        </Table.Cell>
                                        <Table.Cell textAlign="right" fontWeight="bold" color="fg">{stock.quantity.toLocaleString()}</Table.Cell>
                                        <Table.Cell textAlign="right" fontWeight="medium" color="fg.subtle">₩{stock.avg_price.toLocaleString()}</Table.Cell>
                                        <Table.Cell textAlign="right" fontWeight="bold" color="fg">₩{stock.current_price.toLocaleString()}</Table.Cell>
                                        <Table.Cell textAlign="right">
                                            <Badge variant="subtle" colorPalette={stock.profit_rate >= 0 ? "red" : "blue"} borderRadius="md" px={3}>
                                                {stock.profit_rate}%
                                            </Badge>
                                        </Table.Cell>
                                    </Table.Row>
                                ))}
                            </Table.Body>
                        </Table.Root>
                    </Box>
                </Tabs.Content>

                <Tabs.Content value="orders">
                    <Box bg="bg.panel" borderRadius="2xl" border="1px solid" borderColor="border.subtle" overflow="hidden" boxShadow="xs">
                        <Table.Root size="md" variant="line">
                            <Table.Header>
                                <Table.Row bg="bg.muted">
                                    <Table.ColumnHeader color="fg.muted" fontSize="xs" fontWeight="black">ORDER NO</Table.ColumnHeader>
                                    <Table.ColumnHeader color="fg.muted" fontSize="xs" fontWeight="black">STOCK</Table.ColumnHeader>
                                    <Table.ColumnHeader color="fg.muted" fontSize="xs" fontWeight="black">SIDE</Table.ColumnHeader>
                                    <Table.ColumnHeader textAlign="right" color="fg.muted" fontSize="xs" fontWeight="black">ORDER QTY</Table.ColumnHeader>
                                    <Table.ColumnHeader textAlign="right" color="fg.muted" fontSize="xs" fontWeight="black">FILLED</Table.ColumnHeader>
                                    <Table.ColumnHeader textAlign="right" color="fg.muted" fontSize="xs" fontWeight="black">PRICE</Table.ColumnHeader>
                                </Table.Row>
                            </Table.Header>
                            <Table.Body>
                                {orders.map((order) => (
                                    <Table.Row key={order.order_no} _hover={{ bg: "bg.muted" }}>
                                        <Table.Cell fontSize="2xs" fontWeight="bold" color="fg.muted">{order.order_no}</Table.Cell>
                                        <Table.Cell>
                                            <VStack align="start" gap={0}>
                                                <Text fontWeight="800" color="fg">{order.stock_name}</Text>
                                                <Text fontSize="2xs" fontWeight="bold" color="fg.muted">{order.stock_code}</Text>
                                            </VStack>
                                        </Table.Cell>
                                        <Table.Cell>
                                            <Badge variant="solid" colorPalette={order.side === "매수" ? "red" : "blue"} borderRadius="md">
                                                {order.side}
                                            </Badge>
                                        </Table.Cell>
                                        <Table.Cell textAlign="right" fontWeight="bold" color="fg">{order.order_qty.toLocaleString()}</Table.Cell>
                                        <Table.Cell textAlign="right" fontWeight="bold" color="teal.600">{order.filled_qty.toLocaleString()}</Table.Cell>
                                        <Table.Cell textAlign="right" fontWeight="black" color="fg">₩{order.avg_price.toLocaleString()}</Table.Cell>
                                    </Table.Row>
                                ))}
                            </Table.Body>
                        </Table.Root>
                    </Box>
                </Tabs.Content>
            </Tabs.Root>
        </Box>
    );
}
