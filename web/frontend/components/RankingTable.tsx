"use client";

import { Box, Table, Text, VStack, Spinner, HStack, Badge } from "@chakra-ui/react";
import { StockRankItem } from "@/types/stock";
import { ArrowUp, ArrowDown } from "lucide-react";

interface RankingTableProps {
    data: StockRankItem[];
    loading: boolean;
    onSelect: (stock: StockRankItem) => void;
    selectedCode?: string;
}

export function RankingTable({ data, loading, onSelect, selectedCode }: RankingTableProps) {
    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" p={20} bg="bg.panel" borderRadius="xl">
                <Spinner size="xl" color="teal.500" />
            </Box>
        );
    }

    return (
        <Box
            bg="bg.panel"
            borderRadius="xl"
            overflow="hidden"
            maxH="680px"
            overflowY="auto"
            border="1px solid"
            borderColor="border.subtle"
            boxShadow="sm"
        >
            <Table.Root size="md" variant="line" stickyHeader>
                <Table.Header>
                    <Table.Row bg="bg.muted" borderBottom="2px solid" borderColor="border.subtle">
                        <Table.ColumnHeader w="60px" py={5} pl={6} fontSize="2xs" fontWeight="800" color="fg.muted" letterSpacing="widest">#</Table.ColumnHeader>
                        <Table.ColumnHeader py={5} fontSize="2xs" fontWeight="800" color="fg.muted" letterSpacing="widest">INSTRUMENT</Table.ColumnHeader>
                        <Table.ColumnHeader textAlign="right" py={5} fontSize="2xs" fontWeight="800" color="fg.muted" letterSpacing="widest">LAST PRICE</Table.ColumnHeader>
                        <Table.ColumnHeader textAlign="right" py={5} fontSize="2xs" fontWeight="800" color="fg.muted" letterSpacing="widest">CHANGE %</Table.ColumnHeader>
                        <Table.ColumnHeader textAlign="right" py={5} pr={6} fontSize="2xs" fontWeight="800" color="fg.muted" letterSpacing="widest" display={{ base: "none", md: "table-cell" }}>
                            VOLUME
                        </Table.ColumnHeader>
                    </Table.Row>
                </Table.Header>
                <Table.Body>
                    {data.length === 0 ? (
                        <Table.Row>
                            <Table.Cell colSpan={5} textAlign="center" py={20} color="fg.subtle">
                                No data matching your request was found.
                            </Table.Cell>
                        </Table.Row>
                    ) : (
                        data.map((item) => {
                            const isSelected = selectedCode === item.stock_code;
                            const changeRate = item.change_rate;
                            const isUp = changeRate > 0;
                            const isDown = changeRate < 0;
                            const volumeValue = item.volume ?? item.net_buy_qty ?? 0;

                            const statusColor = isUp ? "red.500" : isDown ? "blue.500" : "fg";
                            const statusBg = isUp ? "red.500/5" : isDown ? "blue.500/5" : "transparent";

                            return (
                                <Table.Row
                                    key={item.stock_code}
                                    onClick={() => onSelect(item)}
                                    bg={isSelected ? "teal.500/10" : "transparent"}
                                    _hover={{ bg: isSelected ? "teal.500/15" : "bg.muted" }}
                                    transition="all 0.15s cubic-bezier(.4,0,.2,1)"
                                    cursor="pointer"
                                    borderBottom="1px solid"
                                    borderColor="border.subtle"
                                >
                                    <Table.Cell py={5} pl={6}>
                                        <Text fontWeight="black" color={item.rank <= 3 ? "teal.500" : "fg.muted"} fontSize="xs" fontFamily="mono">
                                            {item.rank.toString().padStart(2, '0')}
                                        </Text>
                                    </Table.Cell>
                                    <Table.Cell py={5}>
                                        <VStack align="start" gap={0.5}>
                                            <Text fontWeight="800" fontSize="sm" color="fg" letterSpacing="tight">
                                                {item.stock_name}
                                            </Text>
                                            <Badge size="sm" variant="subtle" colorPalette="gray" fontSize="2xs" borderRadius="sm">
                                                {item.stock_code}
                                            </Badge>
                                        </VStack>
                                    </Table.Cell>
                                    <Table.Cell textAlign="right" py={5}>
                                        <Text fontWeight="900" fontSize="sm" color="fg" fontFamily="mono">
                                            {item.price.toLocaleString()}
                                        </Text>
                                    </Table.Cell>
                                    <Table.Cell textAlign="right" py={5}>
                                        <Box
                                            display="inline-flex"
                                            alignItems="center"
                                            justifyContent="flex-end"
                                            px={3}
                                            py={1.5}
                                            borderRadius="lg"
                                            bg={statusBg}
                                            color={statusColor}
                                        >
                                            <HStack gap={1}>
                                                {isUp && <ArrowUp size={12} strokeWidth={3} />}
                                                {isDown && <ArrowDown size={12} strokeWidth={3} />}
                                                <Text fontWeight="900" fontSize="xs" fontFamily="mono">
                                                    {Math.abs(item.change_rate).toFixed(2)}%
                                                </Text>
                                            </HStack>
                                        </Box>
                                    </Table.Cell>
                                    <Table.Cell textAlign="right" py={5} pr={6} display={{ base: "none", md: "table-cell" }}>
                                        <Text fontSize="xs" fontWeight="bold" color="fg.subtle" fontFamily="mono">
                                            {volumeValue > 1000000
                                                ? `${(volumeValue / 1000000).toFixed(2)}M`
                                                : volumeValue.toLocaleString()}
                                        </Text>
                                    </Table.Cell>
                                </Table.Row>
                            );
                        })
                    )}
                </Table.Body>
            </Table.Root>
        </Box>
    );
}
