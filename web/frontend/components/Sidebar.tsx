"use client";

import { Box, VStack, Text, Icon, Link, HStack, Separator } from "@chakra-ui/react";
import {
  BarChart3, Bell, CreditCard, LayoutDashboard, Search, Settings,
} from "lucide-react";
import NextLink from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./ThemeToggle";

const MENU = [
  { label: "대시보드", icon: LayoutDashboard, href: "/" },
  { label: "종목 데이터 조회", icon: Search, href: "/search" },
  { label: "데이터 시각화", icon: BarChart3, href: "/visualize" },
  { label: "나의 계좌", icon: CreditCard, href: "/account" },
];

interface SidebarProps {
  collapsed: boolean;
}

export function Sidebar({ collapsed }: SidebarProps) {
  const pathname = usePathname();

  return (
    <Box
      // 넓은 화면: 본문 옆에 붙어 접힘/펼침. 좁은 화면: 접히면 완전히 숨고 펼치면 본문 위로 덮는다.
      w={{ base: collapsed ? "0" : "260px", md: collapsed ? "72px" : "260px" }}
      bg="gray.950"
      h="100vh"
      // 가로 여백은 각 요소가 직접 갖는다 — 선택된 메뉴가 사이드바 폭을 꽉 채우게 하기 위함
      py={{ base: collapsed ? 0 : 6, md: collapsed ? 3 : 6 }}
      px={0}
      position={{ base: "fixed", md: "sticky" }}
      top="0"
      left="0"
      zIndex={100}
      display="flex"
      flexDirection="column"
      color="white"
      borderRight="1px solid"
      borderColor="whiteAlpha.100"
      transition="width 0.2s cubic-bezier(.4,0,.2,1), padding 0.2s cubic-bezier(.4,0,.2,1)"
      flexShrink={0}
      overflow="hidden"
    >
      <VStack align="stretch" gap={8} h="full">
        {/* 로고 — 접기 버튼은 본문 상단 바(AppShell)에 하나만 둔다 */}
        <HStack px={collapsed ? 3 : 6} gap={3} justify={collapsed ? "center" : "flex-start"}>
          <Box
            bg="accent.500"
            w="32px"
            h="32px"
            borderRadius="lg"
            display="flex"
            alignItems="center"
            justifyContent="center"
            flexShrink={0}
          >
            <Text fontWeight="black" fontSize="xs">QM</Text>
          </Box>
          {!collapsed && (
            <Text fontSize="xl" fontWeight="black" letterSpacing="tight" color="white" whiteSpace="nowrap">
              QUANT MINER
            </Text>
          )}
        </HStack>

        {/* 메뉴 — 항목끼리 붙여 두고(gap 0) 좌우 여백 없이 폭을 꽉 채운다 */}
        <VStack align="stretch" gap={0} flex="1">
          {!collapsed && (
            <Text fontSize="xs" fontWeight="bold" color="whiteAlpha.500" px={6} mb={3}>
              MENU
            </Text>
          )}
          {MENU.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                asChild
                key={item.href}
                variant="plain"
                _hover={{ textDecoration: "none" }}
              >
                <NextLink href={item.href} title={collapsed ? item.label : undefined}>
                  <HStack
                    px={collapsed ? 3 : 6}
                    py={3}
                    w="full"
                    borderRadius="none"
                    position="relative"
                    bg={isActive ? "accent.600" : "transparent"}
                    color={isActive ? "white" : "whiteAlpha.700"}
                    _hover={{ bg: isActive ? "accent.600" : "whiteAlpha.100", color: "white" }}
                    cursor="pointer"
                    transition="background-color 0.15s, color 0.15s"
                    justify={collapsed ? "center" : "flex-start"}
                    // 선택 표시는 왼쪽 세로 막대로 — 사각형 배경을 깨지 않는다
                    _before={isActive ? {
                      content: '""',
                      position: "absolute",
                      left: 0,
                      top: 0,
                      bottom: 0,
                      width: "3px",
                      bg: "white",
                    } : undefined}
                  >
                    <Icon as={item.icon} boxSize="5" flexShrink={0} />
                    {!collapsed && (
                      <Text fontWeight={isActive ? "bold" : "medium"} fontSize="sm" whiteSpace="nowrap">
                        {item.label}
                      </Text>
                    )}
                  </HStack>
                </NextLink>
              </Link>
            );
          })}
        </VStack>

        <VStack align="stretch" gap={4}>
          <Separator borderColor="whiteAlpha.200" />
          {collapsed ? (
            <VStack gap={3} px={3} color="whiteAlpha.600" pb={2}>
              <ThemeToggle />
              <Icon as={Bell} boxSize="5" cursor="pointer" _hover={{ color: "white" }} />
              <Icon as={Settings} boxSize="5" cursor="pointer" _hover={{ color: "white" }} />
            </VStack>
          ) : (
            <HStack px={6} pb={2} justify="space-between" color="whiteAlpha.600">
              <ThemeToggle />
              <HStack gap={4}>
                <Icon as={Bell} boxSize="5" cursor="pointer" _hover={{ color: "white" }} />
                <Icon as={Settings} boxSize="5" cursor="pointer" _hover={{ color: "white" }} />
              </HStack>
            </HStack>
          )}
        </VStack>
      </VStack>
    </Box>
  );
}
