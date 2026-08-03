"use client";

import { useMemo, useState } from "react";
import { Box, HStack, Icon, Input, Spinner, Table, Text, VStack } from "@chakra-ui/react";
import {
    ArrowDown,
    ArrowUp,
    BarChart3,
    ChevronLeft,
    ChevronRight,
    Download,
    Filter,
    Inbox,
} from "lucide-react";
import {
    TABLE_CELL,
    TABLE_HEADER_CELL,
    TABLE_HEADER_ROW,
    TABLE_NUM_CELL,
    TABLE_ROW,
    TABLE_SURFACE,
} from "@/lib/table-style";
import { compareRows, downloadCsv, formatCell, toCsv, toNumber } from "./format";
import { GridColumn, GridRow } from "./types";

const PAGE_SIZES = [25, 50, 100, 200];

/** 처음 보여 줄 행 수. 호출부가 "몇 행을 채워야 하는지" 알아야 해서 밖으로 뺀다. */
export const DEFAULT_PAGE_SIZE = 50;

interface DataGridProps {
    columns: GridColumn[];
    rows: GridRow[];
    loading?: boolean;
    error?: string | null;
    /** CSV 파일명 (확장자 제외) */
    exportName?: string;
    emptyMessage?: string;
    /** 그리드 상단 우측에 끼워 넣을 요소 (조회 조건 등) */
    toolbar?: React.ReactNode;
    /** 값의 부호에 따라 빨강/파랑으로 칠할 컬럼 키 */
    signedKeys?: string[];
    /** 지정하면 툴바에 "그래프" 버튼이 생긴다. 정렬·필터가 적용된 행이 넘어간다. */
    onVisualize?: (rows: GridRow[]) => void;
    /** 그래프를 그릴 수 없는 표일 때 사유 (버튼이 비활성화되고 툴팁으로 뜬다) */
    visualizeDisabledReason?: string;
    /**
     * 한 쪽에 보여 줄 행 수가 바뀌면 알려 준다.
     * 받은 행이 이 수에 못 미치면 호출부가 모자란 만큼 더 받아올 수 있다.
     */
    onPageSizeChange?: (size: number) => void;
}

export function DataGrid({
    columns,
    rows,
    loading = false,
    error = null,
    exportName = "data",
    emptyMessage = "조회된 데이터가 없습니다.",
    toolbar,
    signedKeys,
    onVisualize,
    visualizeDisabledReason,
    onPageSizeChange,
}: DataGridProps) {
    const [filter, setFilter] = useState("");
    const [sortKey, setSortKey] = useState<string | null>(null);
    const [sortDesc, setSortDesc] = useState(false);
    const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
    const [page, setPage] = useState(0);

    const signed = useMemo(() => new Set(signedKeys ?? []), [signedKeys]);

    const filtered = useMemo(() => {
        const q = filter.trim().toLowerCase();
        if (!q) return rows;
        return rows.filter(row =>
            columns.some(c => formatCell(c, row).toLowerCase().includes(q))
        );
    }, [rows, filter, columns]);

    const sorted = useMemo(() => {
        if (!sortKey) return filtered;
        const column = columns.find(c => c.key === sortKey);
        if (!column) return filtered;
        return [...filtered].sort((a, b) => compareRows(a, b, column, sortDesc));
    }, [filtered, sortKey, sortDesc, columns]);

    const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize));
    const safePage = Math.min(page, pageCount - 1);
    const visible = sorted.slice(safePage * pageSize, safePage * pageSize + pageSize);

    const toggleSort = (key: string) => {
        if (sortKey !== key) {
            setSortKey(key);
            setSortDesc(true);   // 첫 클릭은 내림차순(최신·큰 값 우선)
        } else if (sortDesc) {
            setSortDesc(false);
        } else {
            setSortKey(null);    // 세 번째 클릭이면 원래 순서로
        }
        setPage(0);
    };

    const cellColor = (column: GridColumn, row: GridRow): string | undefined => {
        if (column.type === "percent" || column.type === "signed" || signed.has(column.key)) {
            const n = toNumber(row[column.key]);
            if (n === null || n === 0) return undefined;
            return n > 0 ? "red.500" : "blue.500";
        }
        return undefined;
    };

    return (
        <VStack align="stretch" gap={3}>
            {/* 툴바 */}
            <HStack justify="space-between" align="center" flexWrap="wrap" gap={3}>
                <HStack gap={3} flexWrap="wrap">
                    <HStack
                        gap={2}
                        bg="bg.muted"
                        borderRadius="xl"
                        px={3}
                        py={1.5}
                        borderWidth="1px"
                        borderColor="border.subtle"
                    >
                        <Icon as={Filter} boxSize="3.5" color="fg.muted" />
                        <Input
                            value={filter}
                            onChange={e => { setFilter(e.target.value); setPage(0); }}
                            placeholder="표 내용 필터"
                            variant="flushed"
                            size="sm"
                            w="160px"
                            border="none"
                            _focusVisible={{ borderColor: "transparent", boxShadow: "none" }}
                            fontWeight="medium"
                        />
                    </HStack>
                    <Text fontSize="xs" fontWeight="black" color="fg.muted" letterSpacing="wider">
                        {sorted.length.toLocaleString()} ROWS
                        {filter && rows.length !== sorted.length && ` / ${rows.length.toLocaleString()}`}
                    </Text>
                </HStack>

                <HStack gap={3} flexWrap="wrap">
                    {toolbar}

                    {onVisualize && (() => {
                        const blocked = !sorted.length || Boolean(visualizeDisabledReason);
                        return (
                            <Box
                                as="button"
                                px={3} py={1.5}
                                borderRadius="lg"
                                bg={blocked ? "bg.muted" : "accent.500"}
                                borderWidth="1px"
                                borderColor={blocked ? "border.subtle" : "accent.500"}
                                fontSize="xs"
                                fontWeight="bold"
                                color={blocked ? "fg.muted" : "white"}
                                cursor={blocked ? "not-allowed" : "pointer"}
                                opacity={blocked ? 0.4 : 1}
                                _hover={blocked ? undefined : { bg: "accent.600", borderColor: "accent.600" }}
                                title={
                                    visualizeDisabledReason ??
                                    (sorted.length ? "지금 보이는 행을 그래프로 그립니다" : undefined)
                                }
                                onClick={() => { if (!blocked) onVisualize(sorted); }}
                            >
                                <HStack gap={1.5}>
                                    <Icon as={BarChart3} boxSize="3.5" />
                                    <Text>그래프로 보기</Text>
                                </HStack>
                            </Box>
                        );
                    })()}

                    <Box
                        as="button"
                        px={3} py={1.5}
                        borderRadius="lg"
                        bg="bg.muted"
                        borderWidth="1px"
                        borderColor="border.subtle"
                        fontSize="xs"
                        fontWeight="bold"
                        color="fg.muted"
                        cursor={sorted.length ? "pointer" : "not-allowed"}
                        opacity={sorted.length ? 1 : 0.4}
                        _hover={sorted.length ? { color: "accent.500", borderColor: "accent.500" } : undefined}
                        onClick={() => sorted.length && downloadCsv(`${exportName}.csv`, toCsv(columns, sorted))}
                    >
                        <HStack gap={1.5}>
                            <Icon as={Download} boxSize="3.5" />
                            <Text>CSV</Text>
                        </HStack>
                    </Box>
                </HStack>
            </HStack>

            {/* 표 */}
            <Box {...TABLE_SURFACE} position="relative">
                {/* 이미 표가 그려져 있으면 덮지 않고 상단 진행 바만 보여 준다.
                    (응답이 오면 표가 사라졌다 나타나지 않고 값만 교체된다) */}
                {loading && rows.length > 0 && (
                    <Box position="absolute" top={0} left={0} right={0} h="2px" zIndex={3} overflow="hidden">
                        <Box
                            h="full"
                            w="40%"
                            bg="accent.500"
                            borderRadius="full"
                            animation="dataGridSweep 1.1s ease-in-out infinite"
                        />
                    </Box>
                )}
                {loading && rows.length === 0 && (
                    <Box
                        position="absolute"
                        inset={0}
                        display="flex"
                        justifyContent="center"
                        alignItems="center"
                        bg="bg.panel/60"
                        backdropFilter="blur(2px)"
                        zIndex={2}
                    >
                        <Spinner color="accent.500" />
                    </Box>
                )}

                {/* 세로로는 자르지 않는다 — 행이 몇이든 그대로 늘어놓고 페이지가 스크롤된다.
                    표 안에 따로 스크롤 영역을 두면 페이지 스크롤과 겹쳐 어느 쪽이 움직이는지
                    헷갈리고, 표 끝을 보려면 좁은 칸 안에서 다시 굴려야 한다.
                    가로만 넘칠 때를 대비해 overflowX는 남긴다(열이 많은 데이터셋). */}
                <Box overflowX="auto">
                    <Table.Root size="sm" variant="line">
                        <Table.Header>
                            <Table.Row {...TABLE_HEADER_ROW}>
                                {columns.map(column => {
                                    const isSorted = sortKey === column.key;
                                    const right = column.type && column.type !== "text" && column.type !== "date" && column.type !== "time";
                                    return (
                                        <Table.ColumnHeader
                                            key={column.key}
                                            {...TABLE_HEADER_CELL}
                                            textAlign={right ? "right" : "left"}
                                            w={column.width}
                                            minW={column.width}
                                            color={isSorted ? "accent.500" : "fg.muted"}
                                            cursor="pointer"
                                            userSelect="none"
                                            _hover={{ color: "accent.500" }}
                                            onClick={() => toggleSort(column.key)}
                                        >
                                            <HStack gap={1} justify={right ? "flex-end" : "flex-start"}>
                                                <Text>{column.label}</Text>
                                                {isSorted && (
                                                    <Icon as={sortDesc ? ArrowDown : ArrowUp} boxSize="3" />
                                                )}
                                            </HStack>
                                        </Table.ColumnHeader>
                                    );
                                })}
                            </Table.Row>
                        </Table.Header>
                        <Table.Body>
                            {visible.map((row, i) => (
                                <Table.Row key={i} {...TABLE_ROW}>
                                    {columns.map(column => {
                                        const right = column.type && column.type !== "text" && column.type !== "date" && column.type !== "time";
                                        return (
                                            <Table.Cell
                                                key={column.key}
                                                {...(right ? TABLE_NUM_CELL : TABLE_CELL)}
                                                color={cellColor(column, row) ?? "fg"}
                                            >
                                                {formatCell(column, row)}
                                            </Table.Cell>
                                        );
                                    })}
                                </Table.Row>
                            ))}
                            {!visible.length && !loading && (
                                <Table.Row>
                                    <Table.Cell colSpan={columns.length} py={16}>
                                        <VStack gap={3}>
                                            <Icon as={Inbox} boxSize="8" color="fg.muted" opacity={0.3} />
                                            <Text fontSize="sm" color="fg.subtle" fontWeight="medium">
                                                {error ?? emptyMessage}
                                            </Text>
                                        </VStack>
                                    </Table.Cell>
                                </Table.Row>
                            )}
                        </Table.Body>
                    </Table.Root>
                </Box>
            </Box>

            {/* 페이지네이션 */}
            <HStack justify="space-between" align="center" flexWrap="wrap" gap={3}>
                <HStack gap={2}>
                    <Text fontSize="2xs" fontWeight="black" color="fg.muted" letterSpacing="wider">
                        ROWS PER PAGE
                    </Text>
                    {PAGE_SIZES.map(size => (
                        <Box
                            key={size}
                            as="button"
                            px={2} py={0.5}
                            borderRadius="md"
                            fontSize="xs"
                            fontWeight="bold"
                            cursor="pointer"
                            bg={pageSize === size ? "accent.500" : "bg.muted"}
                            color={pageSize === size ? "white" : "fg.muted"}
                            onClick={() => {
                                setPageSize(size);
                                setPage(0);
                                onPageSizeChange?.(size);
                            }}
                        >
                            {size}
                        </Box>
                    ))}
                </HStack>

                <HStack gap={2}>
                    <Box
                        as="button"
                        p={1.5}
                        borderRadius="md"
                        bg="bg.muted"
                        color="fg.muted"
                        cursor={safePage > 0 ? "pointer" : "not-allowed"}
                        opacity={safePage > 0 ? 1 : 0.3}
                        onClick={() => safePage > 0 && setPage(safePage - 1)}
                    >
                        <Icon as={ChevronLeft} boxSize="4" />
                    </Box>
                    <Text fontSize="xs" fontWeight="bold" color="fg.subtle" minW="90px" textAlign="center">
                        {safePage + 1} / {pageCount}
                    </Text>
                    <Box
                        as="button"
                        p={1.5}
                        borderRadius="md"
                        bg="bg.muted"
                        color="fg.muted"
                        cursor={safePage < pageCount - 1 ? "pointer" : "not-allowed"}
                        opacity={safePage < pageCount - 1 ? 1 : 0.3}
                        onClick={() => safePage < pageCount - 1 && setPage(safePage + 1)}
                    >
                        <Icon as={ChevronRight} boxSize="4" />
                    </Box>
                </HStack>
            </HStack>
        </VStack>
    );
}
