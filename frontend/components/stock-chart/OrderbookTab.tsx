"use client";

import { Box, Table } from "@chakra-ui/react";
import { STOCK_API } from "@/lib/api-config";
import { OrderbookResponse, StockRankItem } from "@/types/stock";
import { useFetch } from "./useFetch";

interface Props {
    stock: StockRankItem;
}

export function OrderbookTab({ stock }: Props) {
    const { data: orderbook } = useFetch<OrderbookResponse | null>(STOCK_API.ORDERBOOK(stock.stock_code), null);

    return (
        <Box border="1px solid" borderColor="border.subtle" borderRadius="xl" overflow="hidden">
            <Table.Root size="sm">
                <Table.Header>
                    <Table.Row bg="bg.muted">
                        <Table.ColumnHeader textAlign="right" fontSize="2xs" fontWeight="black" color="fg.subtle">ASK RSVP</Table.ColumnHeader>
                        <Table.ColumnHeader textAlign="center" fontSize="2xs" fontWeight="black" color="fg.subtle">PRICE</Table.ColumnHeader>
                        <Table.ColumnHeader textAlign="left" fontSize="2xs" fontWeight="black" color="fg.subtle">BID RSVP</Table.ColumnHeader>
                    </Table.Row>
                </Table.Header>
                <Table.Body>
                    {orderbook?.output1 ? (
                        orderbook.output1.map((item, i) => (
                            <Table.Row key={i} _hover={{ bg: "bg.muted" }}>
                                <Table.Cell textAlign="right" color="blue.500" bg="blue.500/5" fontWeight="bold" fontSize="xs">
                                    {parseInt(item.ask_rsvp).toLocaleString()}
                                </Table.Cell>
                                <Table.Cell textAlign="center" fontWeight="900" fontSize="sm" color="fg">
                                    {parseInt(item.ask_price).toLocaleString()}
                                </Table.Cell>
                                <Table.Cell textAlign="left" color="red.500" bg="red.500/5" fontWeight="bold" fontSize="xs">
                                    {parseInt(item.bid_rsvp).toLocaleString()}
                                </Table.Cell>
                            </Table.Row>
                        ))
                    ) : (
                        <Table.Row>
                            <Table.Cell colSpan={3} textAlign="center" py={10} color="fg.subtle" fontSize="sm">
                                호가 데이터가 없습니다.
                            </Table.Cell>
                        </Table.Row>
                    )}
                </Table.Body>
            </Table.Root>
        </Box>
    );
}
