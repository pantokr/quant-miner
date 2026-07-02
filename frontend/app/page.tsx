"use client";

import { useState } from "react";
import { Box, Grid, GridItem, Tabs, VStack, Heading, Text, Icon, HStack } from "@chakra-ui/react";
import { RankingTable } from "@/components/RankingTable";
import { StockChartDetail } from "@/components/StockChartDetail";
import { useRanking } from "@/hooks/useRanking";
import { StockRankItem } from "@/types/stock";
import { TrendingUp, BarChart3, Globe2, Building2 } from "lucide-react";

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
    <Box p={{ base: 6, lg: 10 }} bg="bg.main" minH="100vh">
      <VStack align="start" mb={8} gap={2}>
        <HStack gap={3}>
          <Box p={2} bg="teal.500" borderRadius="lg" color="white">
            <TrendingUp size={24} />
          </Box>
          <Heading size="2xl" fontWeight="900" color="fg" letterSpacing="tight">
            시장 대시보드
          </Heading>
        </HStack>
        <Text fontSize="md" fontWeight="medium" color="fg.subtle">
          실시간 시장 지표 및 종목별 퀀트 분석 데이터
        </Text>
      </VStack>

      <Tabs.Root value={activeTab} onValueChange={(e) => handleTabChange(e.value)} variant="enclosed">
        <Grid templateColumns={{ base: "1fr", xl: "auto 1fr" }} gap={6} alignItems="center" mb={6}>
          <Tabs.List bg="bg.muted" p={1} borderRadius="2xl" border="none">
            <Tabs.Trigger value="fluctuation" borderRadius="xl" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "teal.600" }} fontSize="sm" fontWeight="bold" px={6}>
              <Icon as={TrendingUp} mr={2} boxSize="4" /> 등락률
            </Tabs.Trigger>
            <Tabs.Trigger value="volume" borderRadius="xl" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "teal.600" }} fontSize="sm" fontWeight="bold" px={6}>
              <Icon as={BarChart3} mr={2} boxSize="4" /> 거래량
            </Tabs.Trigger>
            <Tabs.Trigger value="foreign" borderRadius="xl" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "teal.600" }} fontSize="sm" fontWeight="bold" px={6}>
              <Icon as={Globe2} mr={2} boxSize="4" /> 외국인
            </Tabs.Trigger>
            <Tabs.Trigger value="institution" borderRadius="xl" _selected={{ bg: "bg.panel", boxShadow: "sm", color: "teal.600" }} fontSize="sm" fontWeight="bold" px={6}>
              <Icon as={Building2} mr={2} boxSize="4" /> 기관
            </Tabs.Trigger>
          </Tabs.List>

          <Box justifySelf={{ base: "start", xl: "end" }}>
            <HStack gap={3}>
              <Text fontSize="xs" fontWeight="black" color="fg.muted" letterSpacing="widest">SORT BY</Text>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '12px',
                  border: '1px solid var(--chakra-colors-border-subtle)',
                  fontSize: '13px',
                  fontWeight: '700',
                  outline: 'none',
                  backgroundColor: 'var(--chakra-colors-bg-panel)',
                  color: 'var(--chakra-colors-fg)',
                  cursor: 'pointer',
                  boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
                }}
              >
                {activeTab === "fluctuation" ? (
                  <>
                    <option value="0">상승률 순</option>
                    <option value="1">하락률 순</option>
                    <option value="2">시가대비 상승</option>
                    <option value="3">시가대비 하락</option>
                  </>
                ) : activeTab === "volume" ? (
                  <>
                    <option value="0">평균거래량 순</option>
                    <option value="1">거래증가율 순</option>
                    <option value="2">평균거래회전율 순</option>
                    <option value="3">거래금액 순</option>
                    <option value="4">평균거래금액회전율 순</option>
                  </>
                ) : (
                  <>
                    <option value="0">순매수 수량</option>
                    <option value="1">순매수 금액</option>
                  </>
                )}
              </select>
            </HStack>
          </Box>
        </Grid>
      </Tabs.Root>

      <Grid templateColumns={{ base: "1fr", lg: "1fr 560px" }} gap={8} alignItems="start">
        <GridItem>
          <RankingTable
            data={data}
            loading={loading}
            onSelect={setSelectedStock}
            selectedCode={selectedStock?.stock_code}
          />
        </GridItem>
        <GridItem position={{ lg: "sticky" }} top="24px">
          <StockChartDetail stock={selectedStock} />
        </GridItem>
      </Grid>
    </Box>
  );
}
