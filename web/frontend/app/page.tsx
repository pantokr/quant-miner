"use client";

import { useState } from "react";
import { Box, Grid, GridItem, Tabs, VStack, Heading, Text, Icon } from "@chakra-ui/react";
import { RankingTable, SortOption } from "@/components/RankingTable";
import { StockChartDetail } from "@/components/StockChartDetail";
import { useRanking } from "@/hooks/useRanking";
import { StockRankItem } from "@/types/stock";
import { TrendingUp, BarChart3, Globe2, Building2 } from "lucide-react";

const TABS = [
  { value: "fluctuation", label: "등락률", icon: TrendingUp },
  { value: "volume", label: "거래량", icon: BarChart3 },
  { value: "foreign", label: "외국인", icon: Globe2 },
  { value: "institution", label: "기관", icon: Building2 },
];

/** 탭마다 KIS가 지원하는 정렬 기준이 다르다 */
const SORT_OPTIONS: Record<string, SortOption[]> = {
  fluctuation: [
    { value: "0", label: "상승률 순" },
    { value: "1", label: "하락률 순" },
    { value: "2", label: "시가대비 상승" },
    { value: "3", label: "시가대비 하락" },
  ],
  volume: [
    { value: "0", label: "평균거래량 순" },
    { value: "1", label: "거래증가율 순" },
    { value: "2", label: "평균거래회전율 순" },
    { value: "3", label: "거래금액 순" },
    { value: "4", label: "평균거래금액회전율 순" },
  ],
  foreign: [
    { value: "0", label: "순매수 수량" },
    { value: "1", label: "순매수 금액" },
  ],
  institution: [
    { value: "0", label: "순매수 수량" },
    { value: "1", label: "순매수 금액" },
  ],
};

export default function StockRankingPage() {
  const [activeTab, setActiveTab] = useState("fluctuation");
  const [sort, setSort] = useState("0");
  const [selectedStock, setSelectedStock] = useState<StockRankItem | null>(null);

  const { data, loading } = useRanking(activeTab as any, sort);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    setSort("0"); // 탭 변경 시 정렬 초기화
    setSelectedStock(null);
  };

  return (
    /* 넓은 화면: 한 장에 담고 순위표 안에서만 스크롤(이중 스크롤 방지).
       좁은 화면: 두 패널을 세로로 쌓고 페이지가 스크롤된다. */
    <Box
      px={{ base: 6, lg: 10 }}
      py={{ base: 5, lg: 6 }}
      bg="bg.main"
      h={{ base: "auto", lg: "100%" }}
      minH="100%"
      display="flex"
      flexDirection="column"
      gap={5}
      overflow={{ base: "visible", lg: "hidden" }}
    >
      <VStack align="start" gap={1} flexShrink={0}>
        <Heading size="xl" fontWeight="900" color="fg" letterSpacing="tight">
          시장 대시보드
        </Heading>
        <Text fontSize="sm" fontWeight="medium" color="fg.subtle">
          실시간 시장 지표 및 종목별 퀀트 분석 데이터
        </Text>
      </VStack>

      <Tabs.Root
        value={activeTab}
        onValueChange={(e) => handleTabChange(e.value)}
        variant="enclosed"
        flexShrink={0}
      >
        <Tabs.List bg="bg.muted" p={1} borderRadius="xl" border="none" w="fit-content">
          {TABS.map((t) => (
            <Tabs.Trigger
              key={t.value}
              value={t.value}
              borderRadius="lg"
              _selected={{ bg: "bg.panel", boxShadow: "sm", color: "accent.600" }}
              fontSize="sm"
              fontWeight="bold"
              px={5}
            >
              <Icon as={t.icon} mr={2} boxSize="4" /> {t.label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>
      </Tabs.Root>

      <Grid
        templateColumns={{ base: "1fr", lg: "1fr 1fr" }}
        gap={6}
        flex="1"
        minH={0}
      >
        <GridItem minH={0}>
          <RankingTable
            data={data}
            loading={loading}
            onSelect={setSelectedStock}
            selectedCode={selectedStock?.stock_code}
            sort={sort}
            sortOptions={SORT_OPTIONS[activeTab] ?? SORT_OPTIONS.fluctuation}
            onSortChange={setSort}
          />
        </GridItem>
        <GridItem minH={0} overflowY={{ base: "visible", lg: "auto" }}>
          <StockChartDetail stock={selectedStock} />
        </GridItem>
      </Grid>
    </Box>
  );
}
