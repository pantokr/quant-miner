"use client"

import { Box, Heading, Table, Text } from "@chakra-ui/react"
import {
  TABLE_CELL,
  TABLE_HEADER_CELL,
  TABLE_HEADER_ROW,
  TABLE_NUM_CELL,
  TABLE_ROW,
  TABLE_SURFACE,
} from "@/lib/table-style"

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
  const sign = value >= 0 ? "+" : "-"
  return `${sign}₩${Math.abs(value).toLocaleString("ko-KR")}`
}

export function DataTable() {
  return (
    <Box {...TABLE_SURFACE} p={0}>
      <Heading size="sm" color="fg" fontWeight="bold" px={5} pt={5} pb={3}>
        최근 거래 내역
      </Heading>
      <Table.Root size="sm" variant="line">
        <Table.Header>
          <Table.Row {...TABLE_HEADER_ROW}>
            <Table.ColumnHeader {...TABLE_HEADER_CELL} pl={5}>날짜</Table.ColumnHeader>
            <Table.ColumnHeader {...TABLE_HEADER_CELL}>전략</Table.ColumnHeader>
            <Table.ColumnHeader {...TABLE_HEADER_CELL}>종목</Table.ColumnHeader>
            <Table.ColumnHeader {...TABLE_HEADER_CELL}>방향</Table.ColumnHeader>
            <Table.ColumnHeader {...TABLE_HEADER_CELL} textAlign="right">손익</Table.ColumnHeader>
            <Table.ColumnHeader {...TABLE_HEADER_CELL} pr={5}>상태</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {trades.map((trade, i) => (
            <Table.Row {...TABLE_ROW} key={i}>
              <Table.Cell {...TABLE_CELL} pl={5} color="fg.muted" fontFamily="mono">{trade.date}</Table.Cell>
              <Table.Cell {...TABLE_CELL}>{trade.strategy}</Table.Cell>
              <Table.Cell {...TABLE_CELL} fontWeight="semibold" fontFamily="mono">{trade.symbol}</Table.Cell>
              {/* 방향·상태는 배지 대신 색과 굵기로 — 알약이 줄마다 박히면 표가 시끄럽다 */}
              <Table.Cell {...TABLE_CELL} fontWeight="semibold" color={trade.side === "매수" ? "red.500" : "blue.500"}>
                {trade.side}
              </Table.Cell>
              <Table.Cell {...TABLE_NUM_CELL} fontWeight="semibold" color={trade.pnl >= 0 ? "red.500" : "blue.500"}>
                {formatKRW(trade.pnl)}
              </Table.Cell>
              <Table.Cell {...TABLE_CELL} pr={5}>
                <Text fontSize="2xs" color="fg.muted">{trade.status}</Text>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Box>
  )
}
