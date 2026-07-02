"use client"

import { Box, Heading } from "@chakra-ui/react"
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

const revenueData = [
  { month: "11월", revenue: 18500000 },
  { month: "12월", revenue: 21200000 },
  { month: "1월", revenue: 19800000 },
  { month: "2월", revenue: 23100000 },
  { month: "3월", revenue: 22400000 },
  { month: "4월", revenue: 24350000 },
]

const strategyData = [
  { name: "모멘텀", returns: 15.2 },
  { name: "평균회귀", returns: 8.7 },
  { name: "차익거래", returns: 12.1 },
  { name: "페어트레이딩", returns: 6.4 },
  { name: "머신러닝", returns: 18.9 },
]

function formatKRW(value: number) {
  return `₩${(value / 1000000).toFixed(1)}M`
}

export function RevenueChart() {
  return (
    <Box bg="white" borderRadius="lg" borderWidth="1px" borderColor="gray.200" p={5}>
      <Heading size="sm" color="gray.700" mb={4}>
        월별 수익 추이
      </Heading>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={revenueData} margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
          <defs>
            <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0d9488" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#0d9488" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
          <YAxis tickFormatter={formatKRW} tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
          <Tooltip
            formatter={(value) => [formatKRW(Number(value)), "수익"]}
            contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "13px" }}
          />
          <Area
            type="monotone"
            dataKey="revenue"
            stroke="#0d9488"
            strokeWidth={2}
            fill="url(#revenueGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </Box>
  )
}

export function StrategyChart() {
  return (
    <Box bg="white" borderRadius="lg" borderWidth="1px" borderColor="gray.200" p={5}>
      <Heading size="sm" color="gray.700" mb={4}>
        전략별 수익률 (%)
      </Heading>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={strategyData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} unit="%" />
          <Tooltip
            formatter={(value) => [`${value}%`, "수익률"]}
            contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "13px" }}
          />
          <Bar dataKey="returns" fill="#0d9488" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Box>
  )
}
