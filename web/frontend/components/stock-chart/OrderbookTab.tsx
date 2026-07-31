"use client";

import { Box, HStack, Spinner, Text } from "@chakra-ui/react";
import { STOCK_API } from "@/lib/api-config";
import { StockRankItem } from "@/types/stock";
import { useFetch } from "./useFetch";
import { RefreshButton } from "./RefreshButton";

/**
 * 게이트웨이(/stock/{iscd}/orderbook)가 실제로 돌려주는 모양.
 * types/stock.ts의 OrderbookResponse(output1/output2)는 KIS 원본 형태라 여기선 안 맞는다 —
 * 게이트웨이가 10단계 호가를 배열로 평탄화해서 내려준다.
 */
interface OrderbookPayload {
    ask_prices: number[];
    bid_prices: number[];
    ask_quantities: number[];
    bid_quantities: number[];
    total_ask_qty: number;
    total_bid_qty: number;
    expected_price: string;
}

interface Level {
    price: number;
    qty: number;
    side: "ask" | "bid";
}

interface Props {
    stock: StockRankItem;
}

/** 상단 합계 스트립 높이. 나머지 높이를 호가 행들이 균등하게 나눠 갖는다. */
const SUMMARY_PX = 30;

export function OrderbookTab({ stock }: Props) {
    const { data, loading, reload } = useFetch<OrderbookPayload | null>(
        STOCK_API.ORDERBOOK(stock.stock_code), null,
    );

    // 매도 10단은 높은 가격이 위로, 그 아래에 매수 10단이 높은 가격부터 — 가격축이 이어진다.
    const asks: Level[] = (data?.ask_prices ?? [])
        .map((price, i) => ({ price, qty: data?.ask_quantities?.[i] ?? 0, side: "ask" as const }))
        .filter(l => l.price > 0)
        .reverse();
    const bids: Level[] = (data?.bid_prices ?? [])
        .map((price, i) => ({ price, qty: data?.bid_quantities?.[i] ?? 0, side: "bid" as const }))
        .filter(l => l.price > 0);

    const levels = [...asks, ...bids];
    const maxQty = Math.max(1, ...levels.map(l => l.qty));

    // 종목을 바꾸면 data가 null이 되므로 여기로 들어온다 — 이전 종목 호가를 남기지 않는다
    if (loading && levels.length === 0) {
        return (
            <Box flex="1" display="flex" justifyContent="center" alignItems="center">
                <Spinner size="lg" borderWidth="3px" color="accent.500" />
            </Box>
        );
    }

    if (levels.length === 0) {
        return (
            <Box flex="1" display="flex" justifyContent="center" alignItems="center">
                <Text color="fg.subtle" fontSize="sm" fontWeight="medium">호가 데이터가 없습니다.</Text>
            </Box>
        );
    }

    /*
     * 스크롤을 쓰지 않는다. 20단을 스크롤 안에 밀어 넣으면 정작 볼 구간(현재가 부근)이
     * 접히고, 카드 안에 또 스크롤이 생겨 조작이 번거로워진다.
     * 대신 각 행을 flex=1로 두어 남은 높이를 균등하게 나눠 갖게 한다 —
     * 호가가 몇 단이든(저유동 종목은 10단 미만) 항상 정확히 한 화면에 맞는다.
     */
    const askCount = asks.length;

    return (
        <Box
            flex="1"
            minH={0}
            position="relative"
            border="1px solid"
            borderColor="border.subtle"
            borderRadius="xl"
            overflow="hidden"
            display="flex"
            flexDirection="column"
        >
            <RefreshButton
                onClick={reload}
                busy={loading}
                position="absolute"
                top={1}
                right={1}
                zIndex={2}
            />
            {/* 합계 스트립 — 컬럼 헤더 대신. 색(파랑 매도 / 빨강 매수)이 열을 알려 준다. */}
            <HStack
                justify="space-between"
                px={3}
                h={`${SUMMARY_PX}px`}
                flexShrink={0}
                bg="bg.muted"
                borderBottom="1px solid"
                borderColor="border.subtle"
            >
                <Text fontSize="2xs" fontWeight="black" color="blue.500" fontFamily="mono">
                    매도 {(data?.total_ask_qty ?? 0).toLocaleString()}
                </Text>
                <Text fontSize="2xs" fontWeight="black" color="fg.muted" letterSpacing="wider">
                    호가
                </Text>
                <Text fontSize="2xs" fontWeight="black" color="red.500" fontFamily="mono">
                    매수 {(data?.total_bid_qty ?? 0).toLocaleString()}
                </Text>
            </HStack>

            {levels.map((level, i) => {
                const isAsk = level.side === "ask";
                const color = isAsk ? "blue.500" : "red.500";
                const pct = Math.max(2, (level.qty / maxQty) * 100);
                // 매도 마지막 단과 매수 첫 단 사이 = 현재가 — 여기만 선을 진하게 그어 기준을 준다
                const isBoundary = i === askCount && askCount > 0;

                return (
                    <HStack
                        key={`${level.side}-${level.price}`}
                        flex="1"
                        minH={0}
                        gap={0}
                        borderTop={isBoundary ? "2px solid" : undefined}
                        borderColor={isBoundary ? "fg.muted" : undefined}
                        _hover={{ bg: "bg.muted" }}
                    >
                        {/* 매도 잔량 — 오른쪽(가격) 방향으로 막대가 자란다 */}
                        <Box position="relative" flex="1" h="full">
                            {isAsk && (
                                <>
                                    <Box position="absolute" top="1px" bottom="1px" right={0}
                                        w={`${pct}%`} bg={color} opacity={0.16} borderRadius="sm" />
                                    <HStack position="absolute" inset={0} justify="flex-end" px={2}>
                                        <Text fontSize="2xs" fontWeight="bold" color={color} fontFamily="mono" lineHeight="1">
                                            {level.qty.toLocaleString()}
                                        </Text>
                                    </HStack>
                                </>
                            )}
                        </Box>

                        <Box w="90px" textAlign="center" flexShrink={0}>
                            <Text fontSize="2xs" fontWeight="900" color="fg" fontFamily="mono" lineHeight="1">
                                {level.price.toLocaleString()}
                            </Text>
                        </Box>

                        {/* 매수 잔량 */}
                        <Box position="relative" flex="1" h="full">
                            {!isAsk && (
                                <>
                                    <Box position="absolute" top="1px" bottom="1px" left={0}
                                        w={`${pct}%`} bg={color} opacity={0.16} borderRadius="sm" />
                                    <HStack position="absolute" inset={0} justify="flex-start" px={2}>
                                        <Text fontSize="2xs" fontWeight="bold" color={color} fontFamily="mono" lineHeight="1">
                                            {level.qty.toLocaleString()}
                                        </Text>
                                    </HStack>
                                </>
                            )}
                        </Box>
                    </HStack>
                );
            })}
        </Box>
    );
}
