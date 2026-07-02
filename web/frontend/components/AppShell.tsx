"use client";

import { Box, HStack } from "@chakra-ui/react";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <HStack align="start" gap={0} minH="100vh" bg="bg.main">
      <Sidebar />
      <Box flex="1" h="100vh" overflowY="auto" position="relative">
        {/* 은은한 배경 효과 */}
        <Box
          position="absolute"
          top={0}
          left={0}
          right={0}
          h="500px"
          bgGradient="linear(to-b, teal.500/5, transparent)"
          pointerEvents="none"
        />
        <Box position="relative" zIndex={1}>
          {children}
        </Box>
      </Box>
    </HStack>
  );
}
