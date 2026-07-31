"use client";

import { Box, Spinner, Table, Text, VStack } from "@chakra-ui/react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { STOCK_API } from "@/lib/api-config";
import { StockRankItem } from "@/types/stock";
import { CHART_MARGIN, TOOLTIP_STYLE, Y_TICK_MARGIN, compactPrice } from "./constants";
import { useFetch } from "./useFetch";
import { RefreshButton } from "./RefreshButton";

/**
 * 백엔드(/stock/{iscd}/investor)는 InvestorRow 배열을 그대로 내려준다.
 * 예전 코드는 KIS 원본 형태({output: [{stck_bsop_date, prsn_ntby_qty...}]})를 기대해서
 * 래핑도 필드명도 어긋났고, 그래서 이 탭은 데이터가 있어도 항상 비어 보였다.
 */
interface InvestorRow {
    date: string;              // YYYYMMDD
    individual_net: number;    // 개인 순매수
    foreign_net: number;       // 외국인 순매수
    institution_net: number;   // 기관 순매수
}

const EMPTY: InvestorRow[] = [];
const RECENT_DAYS = 10;   // 그래프에 보여 줄 최근 영업일 수
const TABLE_ROWS = 5;

interface Props {
    stock: StockRankItem;
}

const netColor = (v: number) => (v >= 0 ? "red.500" : "blue.500");
const mmdd = (d: string) => `${d.substring(4, 6)}/${d.substring(6, 8)}`;

export function InvestorTab({ stock }: Props) {
    const { data, loading, reload } = useFetch<InvestorRow[]>(STOCK_API.INVESTOR(stock.stock_code), EMPTY);

    // 응답은 최신순 — 그래프는 과거→현재로 읽히도록 뒤집는다
    const recent = data.slice(0, RECENT_DAYS);
    const chartData = [...recent].reverse();

    return (
        /* 탭 본문(TAB_BODY_H)을 채운다 — 표는 제 높이만 쓰고 나머지를 그래프가 가져간다 */
        <VStack align="stretch" gap={3} flex="1" minH={0} position="relative">
            <RefreshButton
                onClick={reload}
                busy={loading}
                position="absolute"
                top={0}
                right={0}
                zIndex={2}
            />
            <Box flex="1" minH={0}>
                {/* 종목을 바꾸면 데이터가 비므로 여기로 들어온다 — 이전 종목 차트를 남기지 않는다 */}
                {loading && data.length === 0 ? (
                    <Box h="full" display="flex" justifyContent="center" alignItems="center">
                        <Spinner size="lg" borderWidth="3px" color="accent.500" />
                    </Box>
                ) : chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} margin={CHART_MARGIN}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#94a3b8" opacity={0.15} />
                            <XAxis
                                dataKey="date"
                                tickFormatter={mmdd}
                                fontSize={9}
                                fontWeight="bold"
                                tick={{ fill: "#94a3b8" }}
                                tickMargin={8}
                                height={26}
                                tickLine={false}
                            />
                            <YAxis
                                fontSize={9}
                                fontWeight="bold"
                                tick={{ fill: "#94a3b8" }}
                                tickFormatter={compactPrice}
                                width="auto"
                                tickMargin={Y_TICK_MARGIN}
                                tickLine={false}
                                axisLine={false}
                            />
                            {/* 순매수는 부호가 뒤집히는 값이라 0선이 없으면 방향을 읽을 수 없다 */}
                            <ReferenceLine y={0} stroke="#64748b" strokeWidth={1} />
                            <Tooltip
                                contentStyle={TOOLTIP_STYLE}
                                labelFormatter={v => mmdd(String(v))}
                                formatter={(v, name) => [Number(v ?? 0).toLocaleString(), String(name ?? "")]}
                            />
                            <Legend
                                verticalAlign="top"
                                height={20}
                                iconSize={8}
                                wrapperStyle={{ fontSize: 10, fontWeight: 700 }}
                            />
                            <Bar dataKey="foreign_net" name="외국인" fill="#3b82f6" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                            <Bar dataKey="institution_net" name="기관" fill="#ef4444" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                        </BarChart>
                    </ResponsiveContainer>
                ) : (
                    <Box h="full" display="flex" justifyContent="center" alignItems="center">
                        <Text color="fg.subtle" fontSize="sm" fontWeight="medium">
                            수급 데이터가 없습니다.
                        </Text>
                    </Box>
                )}
            </Box>

            {recent.length > 0 && (
                <Box border="1px solid" borderColor="border.subtle" borderRadius="xl" overflow="hidden" flexShrink={0}>
                    <Table.Root size="sm" variant="line">
                        <Table.Header>
                            <Table.Row bg="bg.muted">
                                <Table.ColumnHeader pl={3} fontSize="2xs" fontWeight="black" color="fg.subtle">DATE</Table.ColumnHeader>
                                <Table.ColumnHeader textAlign="right" fontSize="2xs" fontWeight="black" color="fg.subtle">개인</Table.ColumnHeader>
                                <Table.ColumnHeader textAlign="right" fontSize="2xs" fontWeight="black" color="fg.subtle">외국인</Table.ColumnHeader>
                                <Table.ColumnHeader textAlign="right" pr={3} fontSize="2xs" fontWeight="black" color="fg.subtle">기관</Table.ColumnHeader>
                            </Table.Row>
                        </Table.Header>
                        <Table.Body>
                            {recent.slice(0, TABLE_ROWS).map(row => (
                                <Table.Row key={row.date}>
                                    <Table.Cell pl={3} py={1.5} fontSize="2xs" fontWeight="bold" color="fg.muted" fontFamily="mono">
                                        {mmdd(row.date)}
                                    </Table.Cell>
                                    <Table.Cell textAlign="right" py={1.5} fontSize="2xs" fontWeight="bold" fontFamily="mono" color={netColor(row.individual_net)}>
                                        {row.individual_net.toLocaleString()}
                                    </Table.Cell>
                                    <Table.Cell textAlign="right" py={1.5} fontSize="2xs" fontWeight="bold" fontFamily="mono" color={netColor(row.foreign_net)}>
                                        {row.foreign_net.toLocaleString()}
                                    </Table.Cell>
                                    <Table.Cell textAlign="right" pr={3} py={1.5} fontSize="2xs" fontWeight="bold" fontFamily="mono" color={netColor(row.institution_net)}>
                                        {row.institution_net.toLocaleString()}
                                    </Table.Cell>
                                </Table.Row>
                            ))}
                        </Table.Body>
                    </Table.Root>
                </Box>
            )}
        </VStack>
    );
}
