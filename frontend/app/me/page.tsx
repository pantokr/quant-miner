"use client"

import {
  Box,
  SimpleGrid,
  Grid,
  GridItem,
  VStack,
  HStack,
  Text,
  Heading,
  Badge,
  Avatar,
  Separator,
} from "@chakra-ui/react"
import {
  Mail,
  MapPin,
  Calendar,
  Activity,
  TrendingUp,
  TrendingDown,
  BarChart2,
  Percent,
} from "lucide-react"
import { RevenueChart, StrategyChart } from "@/components/Charts"
import { DataTable } from "@/components/DataTable"

const performanceStats = [
  {
    label: "총 실현손익",
    value: "₩24,350,000",
    sub: "+12.5% (지난달 대비)",
    icon: TrendingUp,
    positive: true,
  },
  {
    label: "총 거래 수",
    value: "1,234건",
    sub: "이번 달 142건",
    icon: BarChart2,
    positive: true,
  },
  {
    label: "승률",
    value: "63.4%",
    sub: "783승 / 451패",
    icon: Percent,
    positive: true,
  },
  {
    label: "최대 드로다운",
    value: "-8.2%",
    sub: "2025년 11월 기록",
    icon: TrendingDown,
    positive: false,
  },
]

const strategies = [
  { name: "모멘텀 전략",    returns: "+15.2%", trades: 42,  sharpe: 1.92, status: "활성"   },
  { name: "머신러닝 전략",  returns: "+18.9%", trades: 67,  sharpe: 2.14, status: "활성"   },
  { name: "평균회귀 전략",  returns: "+8.7%",  trades: 38,  sharpe: 1.41, status: "일시정지" },
  { name: "페어트레이딩",   returns: "+6.4%",  trades: 29,  sharpe: 1.08, status: "활성"   },
]

export default function MePage() {
  return (
    <Box p={{ base: 4, md: 6, lg: 8 }}>
      {/* Page header */}
      <VStack align="start" mb={6} gap={1}>
        <Heading size="xl" color="gray.800">
          내 계정
        </Heading>
        <Text fontSize="sm" color="gray.500">
          프로필 및 트레이딩 성과 현황
        </Text>
      </VStack>

      {/* Profile + Performance */}
      <Grid
        templateColumns={{ base: "1fr", lg: "240px 1fr" }}
        gap={5}
        mb={5}
        alignItems="start"
      >
        {/* Profile card */}
        <Box
          bg="white"
          borderRadius="lg"
          borderWidth="1px"
          borderColor="gray.200"
          p={6}
        >
          <VStack gap={4} align="center">
            <Avatar.Root size="2xl">
              <Avatar.Fallback
                name="Pantokr"
                bg="teal.500"
                color="white"
                fontSize="2xl"
                fontWeight="bold"
              />
            </Avatar.Root>

            <VStack gap={1} textAlign="center">
              <Text fontWeight="bold" fontSize="lg" color="gray.800">
                Pantokr
              </Text>
              <Text fontSize="sm" color="gray.500">
                퀀트 트레이더
              </Text>
            </VStack>

            <HStack gap={2} flexWrap="wrap" justify="center">
              <Badge colorPalette="teal" variant="subtle" size="sm">
                퀀트 트레이더
              </Badge>
              <Badge colorPalette="blue" variant="subtle" size="sm">
                알고리즘 전문
              </Badge>
            </HStack>

            <Separator />

            <VStack align="stretch" gap={3} w="full">
              <HStack gap={3} color="gray.500">
                <Mail size={14} />
                <Text fontSize="sm">pantokr@quant-miner.io</Text>
              </HStack>
              <HStack gap={3} color="gray.500">
                <MapPin size={14} />
                <Text fontSize="sm">서울, 대한민국</Text>
              </HStack>
              <HStack gap={3} color="gray.500">
                <Calendar size={14} />
                <Text fontSize="sm">2025년 2월 가입</Text>
              </HStack>
            </VStack>

            <Separator />

            <SimpleGrid columns={2} gap={3} w="full">
              {[
                { label: "샤프 지수", value: "1.84" },
                { label: "운용 기간", value: "14개월" },
                { label: "활성 전략", value: "3개" },
                { label: "총 자산", value: "₩2.1억" },
              ].map((s) => (
                <Box key={s.label} textAlign="center" p={2} bg="gray.50" borderRadius="md">
                  <Text fontSize="xs" color="gray.400">
                    {s.label}
                  </Text>
                  <Text fontSize="sm" fontWeight="700" color="gray.800">
                    {s.value}
                  </Text>
                </Box>
              ))}
            </SimpleGrid>
          </VStack>
        </Box>

        {/* Right column: stats + strategies */}
        <VStack gap={4} align="stretch">
          {/* Performance stats */}
          <SimpleGrid columns={{ base: 2, md: 4 }} gap={4}>
            {performanceStats.map((s) => {
              const Icon = s.icon
              return (
                <Box
                  key={s.label}
                  bg="white"
                  borderRadius="lg"
                  borderWidth="1px"
                  borderColor="gray.200"
                  p={4}
                >
                  <HStack justify="space-between" mb={2}>
                    <Text fontSize="xs" color="gray.500" fontWeight="600">
                      {s.label}
                    </Text>
                    <Icon size={15} color={s.positive ? "#0d9488" : "#ef4444"} />
                  </HStack>
                  <Text
                    fontSize="xl"
                    fontWeight="bold"
                    color={s.positive ? "gray.800" : "red.500"}
                    mb={1}
                  >
                    {s.value}
                  </Text>
                  <Text fontSize="xs" color="gray.400">
                    {s.sub}
                  </Text>
                </Box>
              )
            })}
          </SimpleGrid>

          {/* Active strategies */}
          <Box
            bg="white"
            borderRadius="lg"
            borderWidth="1px"
            borderColor="gray.200"
            p={5}
          >
            <HStack gap={2} mb={4}>
              <Activity size={16} color="#0d9488" />
              <Text fontWeight="600" fontSize="sm" color="gray.700">
                전략 현황
              </Text>
            </HStack>

            <VStack gap={2} align="stretch">
              {strategies.map((s) => (
                <HStack
                  key={s.name}
                  justify="space-between"
                  p={3}
                  bg="gray.50"
                  borderRadius="md"
                  flexWrap="wrap"
                  gap={2}
                >
                  <VStack align="start" gap={0}>
                    <Text fontSize="sm" fontWeight="600" color="gray.800">
                      {s.name}
                    </Text>
                    <Text fontSize="xs" color="gray.400">
                      거래 {s.trades}건 · 샤프 {s.sharpe}
                    </Text>
                  </VStack>
                  <HStack gap={2}>
                    <Text fontSize="sm" fontWeight="700" color="teal.600">
                      {s.returns}
                    </Text>
                    <Badge
                      colorPalette={s.status === "활성" ? "green" : "gray"}
                      variant="subtle"
                      size="sm"
                    >
                      {s.status}
                    </Badge>
                  </HStack>
                </HStack>
              ))}
            </VStack>
          </Box>
        </VStack>
      </Grid>

      {/* Charts */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} gap={4} mb={5}>
        <RevenueChart />
        <StrategyChart />
      </SimpleGrid>

      {/* Trade history */}
      <DataTable />
    </Box>
  )
}
