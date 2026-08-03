"use client";

import { Box, Table, Text, Spinner, HStack } from "@chakra-ui/react";
import { StockRankItem } from "@/types/stock";
import { ArrowUp, ArrowDown } from "lucide-react";
import {
    TABLE_CELL,
    TABLE_HEADER_CELL,
    TABLE_HEADER_ROW,
    TABLE_NUM_CELL,
    TABLE_ROW,
} from "@/lib/table-style";

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
                    <Table.Row {...TABLE_HEADER_ROW}>
                        <Table.ColumnHeader {...TABLE_HEADER_CELL} w="48px" pl={4}>#</Table.ColumnHeader>
                        <Table.ColumnHeader {...TABLE_HEADER_CELL}>INSTRUMENT</Table.ColumnHeader>
                        <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right">LAST PRICE</Table.ColumnHeader>
                        <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right">CHANGE %</Table.ColumnHeader>
                        <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right" pr={4} display={{ base: "none", md: "table-cell" }}>
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

                            const statusColor = isUp ? "red.500" : isDown ? "blue.500" : "fg.subtle";

                            return (
                                // key는 스프레드보다 앞에 둔다 — 뒤에 두면 JSX 컴파일러가
                                // _jsxs 대신 createElement로 폴백해 셀들이 동적 배열로 취급되고,
                                // 셀마다 key가 없다는 경고가 뜬다.
                                <Table.Row
                                    key={item.stock_code}
                                    {...TABLE_ROW}
                                    onClick={() => onSelect(item)}
                                    bg={isSelected ? "accent.500/10" : "transparent"}
                                    _hover={{ bg: isSelected ? "accent.500/15" : "bg.muted" }}
                                    cursor="pointer"
                                >
                                    <Table.Cell {...TABLE_CELL} py={1.5} pl={4} color="fg.muted" fontFamily="mono" fontSize="2xs">
                                        {item.rank.toString().padStart(2, "0")}
                                    </Table.Cell>
                                    {/* 종목명·코드를 한 줄에 나란히 둬서 행 높이를 절반으로 */}
                                    <Table.Cell {...TABLE_CELL} py={1.5}>
                                        <HStack gap={2} minW={0}>
                                            <Text fontWeight="semibold" fontSize="xs" color="fg" truncate>
                                                {item.stock_name}
                                            </Text>
                                            <Text fontSize="2xs" color="fg.muted" fontFamily="mono" flexShrink={0}>
                                                {item.stock_code}
                                            </Text>
                                        </HStack>
                                    </Table.Cell>
                                    <Table.Cell {...TABLE_NUM_CELL} py={1.5} fontFamily="mono">
                                        {item.price.toLocaleString()}
                                    </Table.Cell>
                                    {/* 등락은 색과 화살표로만 — 배경 칩을 걷어 행이 조용해진다 */}
                                    <Table.Cell {...TABLE_NUM_CELL} py={1.5} color={statusColor} fontFamily="mono">
                                        <HStack gap={0.5} justify="flex-end">
                                            {isUp && <ArrowUp size={10} strokeWidth={2.5} />}
                                            {isDown && <ArrowDown size={10} strokeWidth={2.5} />}
                                            <Text fontSize="2xs" fontWeight="semibold" fontFamily="mono">
                                                {Math.abs(item.change_rate).toFixed(2)}%
                                            </Text>
                                        </HStack>
                                    </Table.Cell>
                                    <Table.Cell
                                        {...TABLE_NUM_CELL}
                                        py={1.5}
                                        pr={4}
                                        color="fg.subtle"
                                        fontSize="2xs"
                                        fontFamily="mono"
                                        display={{ base: "none", md: "table-cell" }}
                                    >
                                        {volumeValue > 1000000
                                            ? `${(volumeValue / 1000000).toFixed(2)}M`
                                            : volumeValue.toLocaleString()}
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
