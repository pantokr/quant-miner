"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Badge, Box, HStack, Heading, Icon, Text, VStack } from "@chakra-ui/react";
import { Database, Search, Sparkles } from "lucide-react";
import { DatasetPanel } from "@/components/search/DatasetPanel";
import { DATASETS } from "@/components/search/datasets";
import { SearchBox, SelectedStock } from "@/components/search/SearchBox";
import { StockSummary } from "@/components/search/StockSummary";
import { usePersistentState } from "@/hooks/usePersistentState";
import { MasterStock, stocksByCodes } from "@/lib/stock-search";

const POPULAR_CODES = ["005930", "000660", "373220", "005380", "035420", "068270", "042660", "012450"];

/** useSearchParams는 Suspense 경계 안에서만 프리렌더된다 */
export default function StockSearchPage() {
    return (
        <Suspense fallback={null}>
            <StockSearchView />
        </Suspense>
    );
}

function StockSearchView() {
    const params = useSearchParams();
    const codeParam = params.get("code");
    const nameParam = params.get("name");

    // 새로고침해도 보던 종목·데이터셋이 그대로 남는다
    const [stock, setStock] = usePersistentState<SelectedStock | null>("search-stock", null);
    const [datasetId, setDatasetId] = usePersistentState("search-dataset", DATASETS[0].id);
    const [popular, setPopular] = useState<MasterStock[]>([]);

    // 대시보드에서 ?code=…로 넘어온 경우 그 종목을 연다.
    // 이후 사용자가 다른 종목을 고르면 파라미터가 그대로라 다시 덮어쓰지 않는다.
    useEffect(() => {
        if (!codeParam) return;
        setStock({ code: codeParam, name: nameParam ?? codeParam, market: "" });
    }, [codeParam, nameParam, setStock]);

    const dataset = DATASETS.find(d => d.id === datasetId) ?? DATASETS[0];

    // 인기 종목 이름도 마스터에서 받아 온다 (프론트에 종목명을 하드코딩하지 않기 위해)
    useEffect(() => {
        const controller = new AbortController();
        stocksByCodes(POPULAR_CODES, controller.signal)
            .then(setPopular)
            .catch(() => { /* 마스터 미적재 시 칩만 비워 둔다 */ });
        return () => controller.abort();
    }, []);

    return (
        <Box p={{ base: 6, lg: 10 }} bg="bg.main" minH="100%">
            {/* 헤더 */}
            <VStack align="start" mb={8} gap={2}>
                <HStack gap={3}>
                    <Box p={2} bg="accent.500" borderRadius="lg" color="white">
                        <Search size={24} />
                    </Box>
                    <Heading size="2xl" fontWeight="900" color="fg" letterSpacing="tight">
                        종목 데이터 조회
                    </Heading>
                </HStack>
                <Text fontSize="md" fontWeight="medium" color="fg.subtle">
                    종목별 시세·수급·재무 데이터를 표로 조회하고 CSV로 내려받습니다
                </Text>
            </VStack>

            <VStack align="stretch" gap={8}>
                <SearchBox selected={stock} onSelect={setStock} />

                {!stock ? (
                    /* 초기 상태 — 인기 종목 바로가기 */
                    <Box
                        bg="bg.panel"
                        borderRadius="2xl"
                        borderWidth="1px"
                        borderColor="border.subtle"
                        p={{ base: 8, lg: 16 }}
                        boxShadow="xs"
                    >
                        <VStack gap={6}>
                            <Icon as={Database} boxSize="10" color="fg.muted" opacity={0.3} />
                            <VStack gap={1}>
                                <Text fontSize="md" fontWeight="bold" color="fg">
                                    조회할 종목을 선택하세요
                                </Text>
                                <Text fontSize="sm" color="fg.subtle" fontWeight="medium" textAlign="center">
                                    종목명으로 찾거나 6자리 종목코드를 직접 입력할 수 있습니다.
                                </Text>
                            </VStack>

                            <HStack gap={2} flexWrap="wrap" justify="center" maxW="720px">
                                <HStack gap={1.5} color="fg.muted" mr={1}>
                                    <Icon as={Sparkles} boxSize="3.5" />
                                    <Text fontSize="2xs" fontWeight="black" letterSpacing="wider">POPULAR</Text>
                                </HStack>
                                {popular.map(s => (
                                    <Box
                                        key={s.stock_code}
                                        as="button"
                                        px={4} py={2}
                                        borderRadius="xl"
                                        borderWidth="1px"
                                        borderColor="border.subtle"
                                        bg="bg.muted"
                                        fontSize="sm"
                                        fontWeight="bold"
                                        color="fg.subtle"
                                        cursor="pointer"
                                        _hover={{ borderColor: "accent.500", color: "accent.500" }}
                                        onClick={() => setStock({ code: s.stock_code, name: s.name, market: s.market })}
                                    >
                                        {s.name}
                                    </Box>
                                ))}
                            </HStack>
                        </VStack>
                    </Box>
                ) : (
                    <>
                        <StockSummary stock={stock} />

                        {/* 데이터셋 선택 — 활성 탭만 마운트해 불필요한 KIS 호출을 막는다 */}
                        <VStack align="stretch" gap={5}>
                            <HStack gap={2} flexWrap="wrap">
                                {DATASETS.map(d => {
                                    const active = d.id === datasetId;
                                    return (
                                        <Box
                                            key={d.id}
                                            as="button"
                                            px={4} py={2}
                                            borderRadius="xl"
                                            borderWidth="1px"
                                            borderColor={active ? "accent.500" : "border.subtle"}
                                            bg={active ? "accent.500" : "bg.panel"}
                                            color={active ? "white" : "fg.subtle"}
                                            fontSize="sm"
                                            fontWeight="bold"
                                            cursor="pointer"
                                            transition="all 0.15s"
                                            _hover={active ? undefined : { borderColor: "accent.500", color: "accent.500" }}
                                            onClick={() => setDatasetId(d.id)}
                                        >
                                            <HStack gap={2}>
                                                <Icon as={d.icon} boxSize="4" />
                                                <Text>{d.label}</Text>
                                            </HStack>
                                        </Box>
                                    );
                                })}
                            </HStack>

                            <Box
                                bg="bg.panel"
                                borderRadius="2xl"
                                borderWidth="1px"
                                borderColor="border.subtle"
                                p={{ base: 4, lg: 6 }}
                                boxShadow="xs"
                            >
                                <DatasetPanel
                                    key={`${stock.code}:${dataset.id}`}
                                    dataset={dataset}
                                    stock={stock}
                                />
                            </Box>
                        </VStack>

                        <HStack gap={2} flexWrap="wrap">
                            <Badge variant="subtle" colorPalette="gray" borderRadius="md">
                                공매도·신용잔고는 실전투자 계정에서만 조회됩니다
                            </Badge>
                            <Badge variant="subtle" colorPalette="gray" borderRadius="md">
                                조회한 데이터는 백엔드에서 PostgreSQL에 적재됩니다
                            </Badge>
                        </HStack>
                    </>
                )}
            </VStack>
        </Box>
    );
}
