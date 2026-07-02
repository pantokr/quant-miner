"use client";

import { Box, Table, Text, VStack } from "@chakra-ui/react";
import {
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { STOCK_API } from "@/lib/api-config";
import { InvestorItem, StockRankItem } from "@/types/stock";
import { TOOLTIP_STYLE } from "./constants";
import { useFetch } from "./useFetch";

interface InvestorResponse {
    output?: InvestorItem[];
}

interface Props {
    stock: StockRankItem;
}

export function InvestorTab({ stock }: Props) {
    const { data: response } = useFetch<InvestorResponse | null>(STOCK_API.INVESTOR(stock.stock_code), null);
    const investors = response?.output ?? [];

    return (
        <VStack align="stretch" gap={6}>
            <Box h="220px">
                {investors.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={investors.slice(0, 10).reverse()}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" opacity={0.1} />
                            <XAxis dataKey="stck_bsop_date" tickFormatter={v => v.substring(4)} fontSize={9} fontWeight="bold" tick={{ fill: "#94a3b8" }} />
                            <YAxis fontSize={9} fontWeight="bold" tick={{ fill: "#94a3b8" }} />
                            <Tooltip contentStyle={TOOLTIP_STYLE} />
                            <Bar dataKey="frgn_ntby_qty" name="외국인" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="orgn_ntby_qty" name="기관" fill="#ef4444" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                ) : (
                    <Text textAlign="center" color="fg.subtle" py={10} fontSize="sm">
                        수급 데이터가 없습니다.
                    </Text>
                )}
            </Box>
            {investors.length > 0 && (
                <Table.Root size="sm" variant="line">
                    <Table.Header>
                        <Table.Row bg="bg.muted">
                            <Table.ColumnHeader fontSize="2xs" fontWeight="black" color="fg.subtle">DATE</Table.ColumnHeader>
                            <Table.ColumnHeader textAlign="right" fontSize="2xs" fontWeight="black" color="fg.subtle">IND</Table.ColumnHeader>
                            <Table.ColumnHeader textAlign="right" fontSize="2xs" fontWeight="black" color="fg.subtle">FRG</Table.ColumnHeader>
                            <Table.ColumnHeader textAlign="right" fontSize="2xs" fontWeight="black" color="fg.subtle">INST</Table.ColumnHeader>
                        </Table.Row>
                    </Table.Header>
                    <Table.Body>
                        {investors.slice(0, 5).map((item, i) => (
                            <Table.Row key={i}>
                                <Table.Cell fontSize="2xs" fontWeight="bold" color="fg.muted">
                                    {item.stck_bsop_date.substring(4)}
                                </Table.Cell>
                                <Table.Cell textAlign="right" fontSize="2xs" fontWeight="bold" color={parseInt(item.prsn_ntby_qty) >= 0 ? "red.500" : "blue.500"}>
                                    {parseInt(item.prsn_ntby_qty).toLocaleString()}
                                </Table.Cell>
                                <Table.Cell textAlign="right" fontSize="2xs" fontWeight="bold" color={parseInt(item.frgn_ntby_qty) >= 0 ? "red.500" : "blue.500"}>
                                    {parseInt(item.frgn_ntby_qty).toLocaleString()}
                                </Table.Cell>
                                <Table.Cell textAlign="right" fontSize="2xs" fontWeight="bold" color={parseInt(item.orgn_ntby_qty) >= 0 ? "red.500" : "blue.500"}>
                                    {parseInt(item.orgn_ntby_qty).toLocaleString()}
                                </Table.Cell>
                            </Table.Row>
                        ))}
                    </Table.Body>
                </Table.Root>
            )}
        </VStack>
    );
}
