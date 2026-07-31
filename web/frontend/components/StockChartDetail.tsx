"use client";

import { useRouter } from "next/navigation";
import { Badge, Box, HStack, Icon, Tabs, Text, VStack } from "@chakra-ui/react";
import { ChevronRight, List, TrendingUp, Users } from "lucide-react";
import { usePersistentState } from "@/hooks/usePersistentState";
import { StockRankItem } from "@/types/stock";
import { ChartPeriod, ChartStyle, PERIOD_LABELS, STYLE_LABELS, TAB_BODY_H } from "./stock-chart/constants";
import { MinuteChart } from "./stock-chart/MinuteChart";
import { OhlcvChart } from "./stock-chart/OhlcvChart";
import { OrderbookTab } from "./stock-chart/OrderbookTab";
import { InvestorTab } from "./stock-chart/InvestorTab";

interface StockChartDetailProps {
    stock: StockRankItem | null;
}

/**
 * 카드를 판처럼 띄워 보이게 하는 스타일.
 *
 * 그림자는 한 겹이 아니라 세 겹이다 — 접지(1px)·중간(윤곽)·앰비언트(넓고 옅음).
 * 한 겹짜리 그림자는 "떠 있다"가 아니라 "번졌다"로 읽힌다.
 * 순색 검정 대신 slate(15,23,42)를 깔아 배경의 무채색과 어긋나지 않게 했다.
 * 다크 모드는 그림자가 잘 안 보이므로 윗변 안쪽에 흰 1px(rim light)을 더한다.
 */
const RAISED_CARD = {
    position: "relative" as const,
    bg: "bg.panel",
    borderRadius: "2xl",
    borderWidth: "1px",
    borderColor: "border.subtle",
    // 아래로 번지는 거리를 22px 안쪽으로 묶어 뒀다 — 페이지 하단 여백(24px)을
    // 넘기면 대시보드의 overflow:hidden에 그림자 끝이 잘려 네모나게 보인다.
    boxShadow: [
        "0 1px 1px rgba(15,23,42,0.05)",
        "0 2px 4px -1px rgba(15,23,42,0.07)",
        "0 8px 16px -6px rgba(15,23,42,0.13)",
        "0 18px 36px -14px rgba(15,23,42,0.15)",
    ].join(", "),
    // 광원이 위에 있다는 신호 — 위쪽만 아주 옅게 밝힌다
    backgroundImage: "linear-gradient(180deg, rgba(255,255,255,0.55) 0%, rgba(255,255,255,0) 40%)",
    _dark: {
        borderColor: "whiteAlpha.200",
        boxShadow: [
            "0 1px 1px rgba(0,0,0,0.45)",
            "0 6px 14px -4px rgba(0,0,0,0.55)",
            "0 16px 32px -12px rgba(0,0,0,0.6)",
            "inset 0 1px 0 rgba(255,255,255,0.07)",
        ].join(", "),
        backgroundImage: "linear-gradient(180deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0) 40%)",
    },
    // 윗변 하이라이트 — 모서리까지 긋지 않고 가운데만 밝혀야 금속 테처럼 안 보인다
    _before: {
        content: '""',
        position: "absolute" as const,
        top: 0,
        left: "12%",
        right: "12%",
        height: "1px",
        background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.9), transparent)",
        pointerEvents: "none" as const,
        // 다크에서는 같은 밝기면 흰 줄이 그어진 것처럼 튄다
        _dark: {
            background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.22), transparent)",
        },
    },
};

/** 세그먼트 컨트롤 — 홈(트랙)은 파이고, 선택된 조각만 위로 떠오른다 */
const TAB_TRACK = {
    bg: "bg.muted",
    p: 1,
    borderRadius: "xl",
    borderWidth: "1px",
    borderColor: "border.subtle",
    boxShadow: "inset 0 1px 3px rgba(15,23,42,0.09)",
    w: "fit-content",
    _dark: { boxShadow: "inset 0 1px 4px rgba(0,0,0,0.5)", borderColor: "whiteAlpha.100" },
};

const TAB_SELECTED = {
    bg: "bg.panel",
    color: "accent.500",
    boxShadow: "0 1px 1px rgba(15,23,42,0.08), 0 3px 6px -2px rgba(15,23,42,0.16)",
    _dark: { boxShadow: "0 1px 2px rgba(0,0,0,0.6), 0 4px 10px -3px rgba(0,0,0,0.6)" },
};

/** 기간·형태 토글 — 안 눌린 건 살짝 떠 있고, 눌린 건 안으로 들어간다 */
const RESTING_CHIP = {
    borderWidth: "1px",
    borderColor: "border.subtle",
    boxShadow: "0 1px 1px rgba(15,23,42,0.05), 0 2px 4px -1px rgba(15,23,42,0.09)",
    _hover: {
        transform: "translateY(-1px)",
        boxShadow: "0 2px 3px rgba(15,23,42,0.07), 0 4px 8px -2px rgba(15,23,42,0.13)",
    },
    _dark: {
        borderColor: "whiteAlpha.100",
        boxShadow: "0 1px 2px rgba(0,0,0,0.5), 0 3px 6px -2px rgba(0,0,0,0.5)",
    },
};

const PRESSED_CHIP = {
    borderWidth: "1px",
    borderColor: "transparent",
    transform: "translateY(1px)",
    boxShadow: "inset 0 2px 4px rgba(0,0,0,0.30), inset 0 -1px 0 rgba(255,255,255,0.12)",
};

/** 차트가 앉는 자리 — 카드가 떠 있는 만큼 안쪽은 파인 것처럼 보이게 한다 */
const RECESSED_WELL = {
    bg: "bg.subtle",
    borderRadius: "xl",
    borderWidth: "1px",
    borderColor: "border.subtle",
    boxShadow: "inset 0 2px 4px rgba(15,23,42,0.06), inset 0 -1px 0 rgba(255,255,255,0.7)",
    _dark: {
        bg: "blackAlpha.400",
        borderColor: "whiteAlpha.100",
        boxShadow: "inset 0 2px 6px rgba(0,0,0,0.55)",
    },
};

export function StockChartDetail({ stock }: StockChartDetailProps) {
    const router = useRouter();

    // 새로고침해도 보던 탭·기간·차트 형태가 그대로 남는다
    const [detailTab, setDetailTab] = usePersistentState<string>("detail-tab", "chart");
    const [chartPeriod, setChartPeriod] = usePersistentState<ChartPeriod>("chart-period", "minute");
    const [chartStyle, setChartStyle] = usePersistentState<ChartStyle>("chart-style", "line");

    if (!stock) {
        return (
            <Box {...RAISED_CARD} p={20} textAlign="center">
                <VStack gap={4}>
                    <Icon as={TrendingUp} boxSize="10" color="fg.muted" opacity={0.3} />
                    <Text color="fg.subtle" fontWeight="medium">종목을 선택하여 상세 정보를 확인하세요.</Text>
                </VStack>
            </Box>
        );
    }

    const isUp = stock.change_rate >= 0;
    const color = isUp ? "#ef4444" : "#3b82f6";

    /** 종목 데이터 조회 페이지로 넘긴다 — 이름을 같이 실어 마스터 재조회를 아낀다 */
    const openDetail = () =>
        router.push(`/search?code=${stock.stock_code}&name=${encodeURIComponent(stock.stock_name)}`);

    return (
        <Box {...RAISED_CARD} p={6}>
            <VStack align="stretch" gap={5}>
                {/* 헤더 — 누르면 이 종목의 상세 조회 화면으로 넘어간다.
                    차트 본체는 드래그·휠·탭 조작이 있어 클릭 영역을 헤더로 한정했다. */}
                <HStack
                    as="button"
                    onClick={openDetail}
                    justify="space-between"
                    align="start"
                    textAlign="left"
                    cursor="pointer"
                    borderRadius="xl"
                    mx={-2}
                    px={2}
                    py={2}
                    transition="background 0.15s"
                    _hover={{ bg: "bg.muted" }}
                    aria-label={`${stock.stock_name} 상세 조회`}
                    title="상세 조회로 이동"
                >
                    <VStack align="start" gap={1}>
                        <HStack gap={2}>
                            <Text fontSize="2xl" fontWeight="900" color="fg" letterSpacing="tight">
                                {stock.stock_name}
                            </Text>
                            <Badge size="sm" variant="subtle" colorPalette="gray" borderRadius="md">
                                {stock.stock_code}
                            </Badge>
                        </HStack>
                        <HStack gap={1} color="accent.500">
                            <Text fontSize="xs" fontWeight="bold" letterSpacing="wider">상세 조회</Text>
                            <Icon as={ChevronRight} boxSize="3.5" />
                        </HStack>
                    </VStack>
                    <VStack align="end" gap={0}>
                        <Text fontSize="3xl" fontWeight="900" color="fg" lineHeight="1">
                            {stock.price.toLocaleString()}
                        </Text>
                        <HStack gap={1} mt={1}>
                            <Text fontSize="sm" fontWeight="bold" color={isUp ? "red.500" : "blue.500"}>
                                {isUp ? "+" : ""}{stock.change_rate}%
                            </Text>
                        </HStack>
                    </VStack>
                </HStack>

                <Tabs.Root
                    value={detailTab}
                    onValueChange={(e) => setDetailTab(e.value)}
                    variant="enclosed"
                >
                    {/* 탭 헤더 + 기간 스위치 */}
                    <HStack justify="space-between" align="center" mb={2}>
                        <Tabs.List {...TAB_TRACK}>
                            <Tabs.Trigger value="chart" borderRadius="lg" _selected={TAB_SELECTED} fontSize="xs" fontWeight="bold" px={3} gap={1} transition="all 0.15s">
                                <Icon as={TrendingUp} boxSize="3" />차트
                            </Tabs.Trigger>
                            <Tabs.Trigger value="orderbook" borderRadius="lg" _selected={TAB_SELECTED} fontSize="xs" fontWeight="bold" px={3} gap={1} transition="all 0.15s">
                                <Icon as={List} boxSize="3" />호가
                            </Tabs.Trigger>
                            <Tabs.Trigger value="investor" borderRadius="lg" _selected={TAB_SELECTED} fontSize="xs" fontWeight="bold" px={3} gap={1} transition="all 0.15s">
                                <Icon as={Users} boxSize="3" />투자자
                            </Tabs.Trigger>
                        </Tabs.List>

                        {/* 기간·형태 전환은 차트 탭에서만 의미가 있다.
                            호가·투자자에서는 눌러도 바뀌는 게 없어 혼란만 준다. */}
                        <HStack gap={3} visibility={detailTab === "chart" ? "visible" : "hidden"}>
                            {/* 선/캔들 전환 — 분봉은 봉 폭이 너무 좁아 선만 제공 */}
                            {chartPeriod !== "minute" && (
                                <HStack gap={1}>
                                    {(["line", "candle"] as const).map(s => (
                                        <Box
                                            key={s}
                                            as="button"
                                            px={2.5} py={1}
                                            borderRadius="md"
                                            fontSize="xs"
                                            fontWeight="bold"
                                            cursor="pointer"
                                            bg={chartStyle === s ? "gray.700" : "bg.muted"}
                                            color={chartStyle === s ? "white" : "fg.muted"}
                                            onClick={() => setChartStyle(s)}
                                            transition="all 0.15s"
                                            {...(chartStyle === s ? PRESSED_CHIP : RESTING_CHIP)}
                                        >
                                            {STYLE_LABELS[s]}
                                        </Box>
                                    ))}
                                </HStack>
                            )}
                            <HStack gap={1}>
                                {(["minute", "daily", "monthly", "yearly"] as const).map(p => (
                                    <Box
                                        key={p}
                                        as="button"
                                        px={2.5} py={1}
                                        borderRadius="md"
                                        fontSize="xs"
                                        fontWeight="bold"
                                        cursor="pointer"
                                        bg={chartPeriod === p ? "accent.500" : "bg.muted"}
                                        color={chartPeriod === p ? "white" : "fg.muted"}
                                        onClick={() => setChartPeriod(p)}
                                        transition="all 0.15s"
                                        {...(chartPeriod === p ? PRESSED_CHIP : RESTING_CHIP)}
                                    >
                                        {PERIOD_LABELS[p]}
                                    </Box>
                                ))}
                            </HStack>
                        </HStack>
                    </HStack>

                    {/* 세 탭 모두 같은 높이의 상자를 쓴다 — 탭을 옮겨도 카드가 출렁이지 않는다.
                        내용은 각 탭이 이 높이를 채우도록(flex) 스스로 조정한다. */}
                    <Tabs.Content value="chart" pt={2}>
                        {/* 차트를 파인 면 위에 앉혀서 카드가 떠 있다는 인상을 강화한다 */}
                        <Box {...RECESSED_WELL} px={2} py={3} h={TAB_BODY_H} display="flex" flexDirection="column">
                            {chartPeriod === "minute" ? (
                                <MinuteChart stock={stock} color={color} />
                            ) : (
                                <OhlcvChart stock={stock} period={chartPeriod} color={color} style={chartStyle} />
                            )}
                        </Box>
                    </Tabs.Content>

                    <Tabs.Content value="orderbook" pt={2}>
                        <Box h={TAB_BODY_H} display="flex" flexDirection="column">
                            <OrderbookTab stock={stock} />
                        </Box>
                    </Tabs.Content>

                    <Tabs.Content value="investor" pt={2}>
                        <Box h={TAB_BODY_H} display="flex" flexDirection="column">
                            <InvestorTab stock={stock} />
                        </Box>
                    </Tabs.Content>
                </Tabs.Root>
            </VStack>
        </Box>
    );
}
