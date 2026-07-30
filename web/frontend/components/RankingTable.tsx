"use client";

import { Box, Table, Text, Spinner, HStack } from "@chakra-ui/react";
import { StockRankItem } from "@/types/stock";
import { ArrowUp, ArrowDown } from "lucide-react";

export interface SortOption {
    value: string;
    label: string;
}

interface RankingTableProps {
    data: StockRankItem[];
    loading: boolean;
    onSelect: (stock: StockRankItem) => void;
    selectedCode?: string;
    /** 정렬 기준 — 표 헤더 안에 함께 둔다 */
    sort: string;
    sortOptions: SortOption[];
    onSortChange: (value: string) => void;
}

const selectStyle: React.CSSProperties = {
    padding: "6px 12px",
    borderRadius: "8px",
    border: "1px solid var(--chakra-colors-border-subtle)",
    fontSize: "12px",
    fontWeight: 700,
    outline: "none",
    backgroundColor: "var(--chakra-colors-bg-panel)",
    color: "var(--chakra-colors-fg)",
    cursor: "pointer",
};

export function RankingTable({
    data, loading, onSelect, selectedCode, sort, sortOptions, onSortChange,
}: RankingTableProps) {
    return (
        <Box
            bg="bg.panel"
            borderRadius="xl"
            border="1px solid"
            borderColor="border.subtle"
            boxShadow="sm"
            h={{ base: "auto", lg: "100%" }}
            display="flex"
            flexDirection="column"
            overflow="hidden"
        >
            {/* 표 헤더 — 정렬 기준을 표와 같은 카드 안에 둔다 */}
            <HStack
                justify="space-between"
                align="center"
                px={4}
                py={3}
                gap={3}
                flexShrink={0}
                borderBottom="1px solid"
                borderColor="border.subtle"
            >
                <Text fontSize="xs" fontWeight="black" color="fg.muted" letterSpacing="wider">
                    {data.length}개 종목
                </Text>
                <HStack gap={2}>
                    <Text fontSize="2xs" fontWeight="black" color="fg.muted" letterSpacing="wider">
                        SORT BY
                    </Text>
                    <select value={sort} onChange={e => onSortChange(e.target.value)} style={selectStyle}>
                        {sortOptions.map(o => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                    </select>
                </HStack>
            </HStack>

            {loading ? (
                <Box flex="1" display="flex" justifyContent="center" alignItems="center" py={20}>
                    <Spinner size="xl" color="accent.500" />
                </Box>
            ) : (
                /* 스크롤은 이 안에서만 — 페이지는 스크롤되지 않는다 */
                <Box flex="1" minH={0} overflowY="auto" maxH={{ base: "60vh", lg: "none" }}>
            <Table.Root size="sm" variant="line" stickyHeader>
                <Table.Header>
                    <Table.Row bg="bg.muted" borderBottom="2px solid" borderColor="border.subtle">
                        <Table.ColumnHeader w="48px" py={2.5} pl={4} fontSize="2xs" fontWeight="800" color="fg.muted" letterSpacing="widest">#</Table.ColumnHeader>
                        <Table.ColumnHeader py={2.5} fontSize="2xs" fontWeight="800" color="fg.muted" letterSpacing="widest">INSTRUMENT</Table.ColumnHeader>
                        <Table.ColumnHeader textAlign="right" py={2.5} fontSize="2xs" fontWeight="800" color="fg.muted" letterSpacing="widest">LAST PRICE</Table.ColumnHeader>
                        <Table.ColumnHeader textAlign="right" py={2.5} fontSize="2xs" fontWeight="800" color="fg.muted" letterSpacing="widest">CHANGE %</Table.ColumnHeader>
                        <Table.ColumnHeader textAlign="right" py={2.5} pr={4} fontSize="2xs" fontWeight="800" color="fg.muted" letterSpacing="widest" display={{ base: "none", md: "table-cell" }}>
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
                                    bg={isSelected ? "accent.500/10" : "transparent"}
                                    _hover={{ bg: isSelected ? "accent.500/15" : "bg.muted" }}
                                    transition="all 0.15s cubic-bezier(.4,0,.2,1)"
                                    cursor="pointer"
                                    borderBottom="1px solid"
                                    borderColor="border.subtle"
                                >
                                    <Table.Cell py={1.5} pl={4}>
                                        <Text fontWeight="black" color={item.rank <= 3 ? "accent.500" : "fg.muted"} fontSize="2xs" fontFamily="mono">
                                            {item.rank.toString().padStart(2, '0')}
                                        </Text>
                                    </Table.Cell>
                                    {/* 종목명·코드를 한 줄에 나란히 둬서 행 높이를 절반으로 */}
                                    <Table.Cell py={1.5}>
                                        <HStack gap={2} minW={0}>
                                            <Text fontWeight="800" fontSize="xs" color="fg" letterSpacing="tight" truncate>
                                                {item.stock_name}
                                            </Text>
                                            <Text fontSize="2xs" fontWeight="bold" color="fg.muted" fontFamily="mono" flexShrink={0}>
                                                {item.stock_code}
                                            </Text>
                                        </HStack>
                                    </Table.Cell>
                                    <Table.Cell textAlign="right" py={1.5}>
                                        <Text fontWeight="900" fontSize="xs" color="fg" fontFamily="mono">
                                            {item.price.toLocaleString()}
                                        </Text>
                                    </Table.Cell>
                                    <Table.Cell textAlign="right" py={1.5}>
                                        <Box
                                            display="inline-flex"
                                            alignItems="center"
                                            justifyContent="flex-end"
                                            px={2}
                                            py={0.5}
                                            borderRadius="md"
                                            bg={statusBg}
                                            color={statusColor}
                                        >
                                            <HStack gap={0.5}>
                                                {isUp && <ArrowUp size={10} strokeWidth={3} />}
                                                {isDown && <ArrowDown size={10} strokeWidth={3} />}
                                                <Text fontWeight="900" fontSize="2xs" fontFamily="mono">
                                                    {Math.abs(item.change_rate).toFixed(2)}%
                                                </Text>
                                            </HStack>
                                        </Box>
                                    </Table.Cell>
                                    <Table.Cell textAlign="right" py={1.5} pr={4} display={{ base: "none", md: "table-cell" }}>
                                        <Text fontSize="2xs" fontWeight="bold" color="fg.subtle" fontFamily="mono">
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
            )}
        </Box>
    );
}
