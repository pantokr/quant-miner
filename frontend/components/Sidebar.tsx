"use client";

import { Box, VStack, Text, Icon, Link, HStack, Separator } from "@chakra-ui/react";
import { TrendingUp, CreditCard, LayoutDashboard, Settings, Bell } from "lucide-react";
import NextLink from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./ThemeToggle";

export function Sidebar() {
  const pathname = usePathname();

  const menuItems = [
    { label: "대시보드", icon: LayoutDashboard, href: "/" },
    { label: "나의 계좌", icon: CreditCard, href: "/account" },
  ];

  return (
    <Box
      w="260px"
      bg="gray.950"
      h="100vh"
      p={6}
      position="sticky"
      top="0"
      display={{ base: "none", md: "flex" }}
      flexDirection="column"
      color="white"
      borderRight="1px solid"
      borderColor="whiteAlpha.100"
    >
      <VStack align="stretch" gap={8} h="full">
        <HStack px={2} gap={3}>
          <Box
            bg="teal.500"
            w="32px"
            h="32px"
            borderRadius="lg"
            display="flex"
            alignItems="center"
            justifyContent="center"
          >
            <Text fontWeight="black" fontSize="xs">QM</Text>
          </Box>
          <Text fontSize="xl" fontWeight="black" letterSpacing="tight" color="white">
            QUANT MINER
          </Text>
        </HStack>

        <VStack align="stretch" gap={2} flex="1">
          <Text fontSize="xs" fontWeight="bold" color="whiteAlpha.500" px={2} mb={2}>
            MENU
          </Text>
          {menuItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                asChild
                key={item.href}
                variant="plain"
                _hover={{ textDecoration: "none" }}
              >
                <NextLink href={item.href}>
                  <HStack
                    p={3}
                    borderRadius="xl"
                    bg={isActive ? "teal.500" : "transparent"}
                    color={isActive ? "white" : "whiteAlpha.700"}
                    _hover={{ bg: isActive ? "teal.600" : "whiteAlpha.100", color: "white" }}
                    cursor="pointer"
                    transition="all 0.2s cubic-bezier(.4,0,.2,1)"
                  >
                    <Icon as={item.icon} boxSize="5" />
                    <Text fontWeight={isActive ? "bold" : "medium"} fontSize="sm">
                      {item.label}
                    </Text>
                  </HStack>
                </NextLink>
              </Link>
            );
          })}
        </VStack>

        <VStack align="stretch" gap={4}>
          <Separator borderColor="whiteAlpha.200" />
          <HStack px={2} justify="space-between" color="whiteAlpha.600">
            <ThemeToggle />
            <HStack gap={4}>
              <Icon as={Bell} boxSize="5" cursor="pointer" _hover={{ color: "white" }} />
              <Icon as={Settings} boxSize="5" cursor="pointer" _hover={{ color: "white" }} />
            </HStack>
          </HStack>
          <HStack gap={3} px={2} py={4}>
            <Box w="36px" h="36px" borderRadius="full" bg="whiteAlpha.200" border="1px solid" borderColor="whiteAlpha.300" />
            <VStack align="start" gap={0}>
              <Text fontSize="sm" fontWeight="bold">Investor</Text>
              <Text fontSize="xs" color="whiteAlpha.500">Free Plan</Text>
            </VStack>
          </HStack>
        </VStack>
      </VStack>
    </Box>
  );
}
