"use client"

import { Box, Heading, Table, Badge } from "@chakra-ui/react"

const trades = [
  { date: "2026-04-14", strategy: "모멘텀", symbol: "AAPL", side: "매수", pnl: 1250000, status: "완료" },
  { date: "2026-04-14", strategy: "머신러닝", symbol: "NVDA", side: "매도", pnl: 3120000, status: "완료" },
  { date: "2026-04-13", strategy: "평균회귀", symbol: "TSLA", side: "매수", pnl: -480000, status: "완료" },
  { date: "2026-04-13", strategy: "차익거래", symbol: "MSFT", side: "매수", pnl: 890000, status: "완료" },
  { date: "2026-04-12", strategy: "모멘텀", symbol: "GOOGL", side: "매도", pnl: 2340000, status: "완료" },
  { date: "2026-04-12", strategy: "페어트레이딩", symbol: "META", side: "매수", pnl: -210000, status: "완료" },
  { date: "2026-04-11", strategy: "머신러닝", symbol: "AMZN", side: "매수", pnl: 1780000, status: "완료" },
  { date: "2026-04-11", strategy: "평균회귀", symbol: "NFLX", side: "매도", pnl: 650000, status: "완료" },
]

function formatKRW(value: number) {
  const sign = value >= 0 ? "+" : ""
  return `${sign}₩${Math.abs(value).toLocaleString("ko-KR")}`
}

export function DataTable() {
  return (
    <Box bg="white" borderRadius="lg" borderWidth="1px" borderColor="gray.200" p={5}>
      <Heading size="sm" color="gray.700" mb={4}>
        최근 거래 내역
      </Heading>
      <Table.Root size="sm">
        <Table.Header>
          <Table.Row bg="gray.50">
            <Table.ColumnHeader color="gray.500" fontWeight="600" fontSize="xs">날짜</Table.ColumnHeader>
            <Table.ColumnHeader color="gray.500" fontWeight="600" fontSize="xs">전략</Table.ColumnHeader>
            <Table.ColumnHeader color="gray.500" fontWeight="600" fontSize="xs">종목</Table.ColumnHeader>
            <Table.ColumnHeader color="gray.500" fontWeight="600" fontSize="xs">방향</Table.ColumnHeader>
            <Table.ColumnHeader color="gray.500" fontWeight="600" fontSize="xs" textAlign="right">손익</Table.ColumnHeader>
            <Table.ColumnHeader color="gray.500" fontWeight="600" fontSize="xs">상태</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {trades.map((trade, i) => (
            <Table.Row key={i} _hover={{ bg: "gray.50" }}>
              <Table.Cell fontSize="sm" color="gray.500">{trade.date}</Table.Cell>
              <Table.Cell fontSize="sm" fontWeight="500">{trade.strategy}</Table.Cell>
              <Table.Cell fontSize="sm" fontWeight="600" color="gray.700">{trade.symbol}</Table.Cell>
              <Table.Cell>
                <Badge
                  colorPalette={trade.side === "매수" ? "blue" : "orange"}
                  size="sm"
                  variant="subtle"
                >
                  {trade.side}
                </Badge>
              </Table.Cell>
              <Table.Cell textAlign="right" fontSize="sm" fontWeight="600" color={trade.pnl >= 0 ? "teal.600" : "red.500"}>
                {formatKRW(trade.pnl)}
              </Table.Cell>
              <Table.Cell>
                <Badge colorPalette="gray" size="sm" variant="subtle">
                  {trade.status}
                </Badge>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  )
}
