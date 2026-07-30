"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Box, Grid, HStack, Icon, Spinner, Text, VStack } from "@chakra-ui/react";
import { AlertTriangle, BarChart3 } from "lucide-react";
import { STOCK_API } from "@/lib/api-config";
import { CurrentPriceResponse } from "@/types/stock";
import { sendToVisualize } from "@/components/visualize/handoff";
import { SelectedStock } from "./SearchBox";
import { useDataset } from "./useDataset";

interface OrderbookResponse {
    ask_prices: number[];
    bid_prices: number[];
    ask_quantities: number[];
    bid_quantities: number[];
    total_ask_qty: number;
    total_bid_qty: number;
    expected_price: string;
}

interface Row {
    price: number;
    qty: number;
    side: "ask" | "bid";
}

/** 잔량 막대 — 최대 잔량 대비 비율로 폭을 잡는다. */
function QtyBar({ qty, max, side }: { qty: number; max: number; side: "ask" | "bid" }) {
    const pct = max > 0 ? Math.max(2, (qty / max) * 100) : 0;
    const color = side === "ask" ? "blue.500" : "red.500";
    return (
        <Box position="relative" h="26px" w="full">
            <Box
                position="absolute"
                top="3px"
                bottom="3px"
                {...(side === "ask" ? { right: 0 } : { left: 0 })}
                w={`${pct}%`}
                bg={color}
                opacity={0.16}
                borderRadius="sm"
            />
            <HStack
                position="absolute"
                inset={0}
                justify={side === "ask" ? "flex-end" : "flex-start"}
                px={3}
            >
                <Text fontSize="xs" fontWeight="bold" color={color} fontVariantNumeric="tabular-nums">
                    {qty.toLocaleString()}
                </Text>
            </HStack>
        </Box>
    );
}

export function OrderbookBoard({ stock }: { stock: SelectedStock }) {
    const book = useDataset(STOCK_API.ORDERBOOK(stock.code));
    const quote = useDataset(STOCK_API.CURRENT(stock.code));
    const [note, setNote] = useState("");
    const router = useRouter();

    const ob = book.data as OrderbookResponse | null;
    const current = (quote.data as CurrentPriceResponse | null)?.current ?? 0;

    if (book.error) {
        return (
            <Box py={14} textAlign="center">
                <Text fontSize="sm" color="fg.subtle" fontWeight="medium">{book.error}</Text>
            </Box>
        );
    }
    if (!ob?.ask_prices?.length) {
        return (
            <Box py={14} textAlign="center">
                {book.loading ? <Spinner color="accent.500" /> : (
                    <Text fontSize="sm" color="fg.subtle" fontWeight="medium">
                        호가 데이터가 없습니다. (장 시작 전·종료 후에는 비어 있을 수 있습니다)
                    </Text>
                )}
            </Box>
        );
    }

    // 매도호가는 높은 가격이 위로 오도록 뒤집고, 그 아래에 매수호가를 붙인다.
    const asks: Row[] = ob.ask_prices
        .map((price, i) => ({ price, qty: ob.ask_quantities?.[i] ?? 0, side: "ask" as const }))
        .reverse();
    const bids: Row[] = ob.bid_prices
        .map((price, i) => ({ price, qty: ob.bid_quantities?.[i] ?? 0, side: "bid" as const }));

    const rows = [...asks, ...bids];
    const maxQty = Math.max(1, ...rows.map(r => r.qty));

    const totalAsk = ob.total_ask_qty ?? 0;
    const totalBid = ob.total_bid_qty ?? 0;
    const totalMax = Math.max(1, totalAsk, totalBid);

    /** 사다리를 그대로 표로 펴서 시각화 페이지로 넘긴다 (호가 단계별 잔량 막대그래프용). */
    const toVisualize = () => {
        const table = rows.map((r, i) => ({
            단계: r.side === "ask" ? `매도${asks.length - i}` : `매수${i - asks.length + 1}`,
            호가: r.price,
            매도잔량: r.side === "ask" ? r.qty : 0,
            매수잔량: r.side === "bid" ? r.qty : 0,
            구분: r.side === "ask" ? "매도" : "매수",
        }));
        const result = sendToVisualize(`${stock.name} · 호가`, table);
        if (!result.ok) {
            setNote(result.error ?? "그래프로 넘기지 못했습니다.");
            return;
        }
        router.push("/visualize");
    };

    return (
        <VStack align="stretch" gap={4}>
            {book.loading && (
                <Box h="2px" overflow="hidden" borderRadius="full">
                    <Box h="full" w="40%" bg="accent.500" animation="dataGridSweep 1.1s ease-in-out infinite" />
                </Box>
            )}

            <HStack justify="flex-end">
                <Box
                    as="button"
                    px={3} py={1.5}
                    borderRadius="lg"
                    bg="accent.500"
                    borderWidth="1px"
                    borderColor="accent.500"
                    color="white"
                    fontSize="xs"
                    fontWeight="bold"
                    cursor="pointer"
                    _hover={{ bg: "accent.600", borderColor: "accent.600" }}
                    title="호가 단계별 잔량을 그래프로 그립니다"
                    onClick={toVisualize}
                >
                    <HStack gap={1.5}>
                        <Icon as={BarChart3} boxSize="3.5" />
                        <Text>그래프로 보기</Text>
                    </HStack>
                </Box>
            </HStack>

            {note && (
                <HStack
                    gap={2}
                    bg="orange.500/10"
                    borderWidth="1px"
                    borderColor="orange.500/30"
                    borderRadius="xl"
                    px={4} py={2.5}
                >
                    <Icon as={AlertTriangle} boxSize="3.5" color="orange.500" flexShrink={0} />
                    <Text fontSize="xs" fontWeight="medium" color="fg.subtle">{note}</Text>
                </HStack>
            )}

            {/* 헤더 */}
            <Grid templateColumns="1fr 130px 1fr" alignItems="center" px={1}>
                <Text fontSize="2xs" fontWeight="black" color="blue.500" letterSpacing="wider" textAlign="right">
                    매도잔량
                </Text>
                <Text fontSize="2xs" fontWeight="black" color="fg.muted" letterSpacing="wider" textAlign="center">
                    호가
                </Text>
                <Text fontSize="2xs" fontWeight="black" color="red.500" letterSpacing="wider">
                    매수잔량
                </Text>
            </Grid>

            {/* 호가 사다리 */}
            <Box borderWidth="1px" borderColor="border.subtle" borderRadius="xl" overflow="hidden">
                {rows.map((row, i) => {
                    const isBoundary = i === asks.length;   // 매도/매수 경계
                    const isCurrent = current > 0 && row.price === current;
                    return (
                        <Grid
                            key={`${row.side}-${row.price}`}
                            templateColumns="1fr 130px 1fr"
                            alignItems="center"
                            borderTopWidth={isBoundary ? "2px" : i === 0 ? "0" : "1px"}
                            borderTopColor={isBoundary ? "border.emphasized" : "border.subtle"}
                            bg={isCurrent ? "accent.500/10" : undefined}
                        >
                            {/* 매도잔량 (왼쪽) */}
                            <Box>{row.side === "ask" && <QtyBar qty={row.qty} max={maxQty} side="ask" />}</Box>

                            {/* 가격 (가운데) */}
                            <Box
                                textAlign="center"
                                py={1}
                                borderLeftWidth="1px"
                                borderRightWidth="1px"
                                borderColor="border.subtle"
                                bg={isCurrent ? "transparent" : "bg.muted"}
                            >
                                <Text
                                    fontSize="sm"
                                    fontWeight="900"
                                    color={isCurrent ? "accent.500" : row.side === "ask" ? "blue.600" : "red.600"}
                                    fontVariantNumeric="tabular-nums"
                                >
                                    {row.price.toLocaleString()}
                                </Text>
                            </Box>

                            {/* 매수잔량 (오른쪽) */}
                            <Box>{row.side === "bid" && <QtyBar qty={row.qty} max={maxQty} side="bid" />}</Box>
                        </Grid>
                    );
                })}
            </Box>

            {/* 총 잔량 비교 */}
            <VStack align="stretch" gap={2}>
                <Grid templateColumns="1fr 130px 1fr" alignItems="center">
                    <Box>
                        <Box h="10px" bg="bg.muted" borderRadius="full" overflow="hidden" position="relative">
                            <Box
                                position="absolute" right={0} top={0} bottom={0}
                                w={`${(totalAsk / totalMax) * 100}%`}
                                bg="blue.500" opacity={0.7}
                            />
                        </Box>
                    </Box>
                    <Text fontSize="2xs" fontWeight="black" color="fg.muted" textAlign="center" letterSpacing="wider">
                        총잔량
                    </Text>
                    <Box>
                        <Box h="10px" bg="bg.muted" borderRadius="full" overflow="hidden" position="relative">
                            <Box
                                position="absolute" left={0} top={0} bottom={0}
                                w={`${(totalBid / totalMax) * 100}%`}
                                bg="red.500" opacity={0.7}
                            />
                        </Box>
                    </Box>
                </Grid>
                <Grid templateColumns="1fr 130px 1fr" alignItems="center">
                    <Text fontSize="xs" fontWeight="bold" color="blue.500" textAlign="right" fontVariantNumeric="tabular-nums">
                        {totalAsk.toLocaleString()}
                    </Text>
                    <Text fontSize="2xs" fontWeight="bold" color="fg.subtle" textAlign="center">
                        {totalBid > totalAsk ? "매수 우위" : totalAsk > totalBid ? "매도 우위" : "균형"}
                    </Text>
                    <Text fontSize="xs" fontWeight="bold" color="red.500" fontVariantNumeric="tabular-nums">
                        {totalBid.toLocaleString()}
                    </Text>
                </Grid>
            </VStack>

            {ob.expected_price && Number(ob.expected_price) > 0 && (
                <HStack justify="center" gap={2}>
                    <Text fontSize="2xs" fontWeight="black" color="fg.muted" letterSpacing="wider">
                        예상체결가
                    </Text>
                    <Text fontSize="sm" fontWeight="900" color="fg" fontVariantNumeric="tabular-nums">
                        {Number(ob.expected_price).toLocaleString()}
                    </Text>
                </HStack>
            )}
        </VStack>
    );
}
