"use client";

import { useEffect, useState } from "react";
import { Box, HStack, Icon, Text } from "@chakra-ui/react";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { Sidebar } from "./Sidebar";

const COLLAPSE_KEY = "quant-miner:sidebar-collapsed";

export function AppShell({ children }: { children: React.ReactNode }) {
    const [collapsed, setCollapsed] = useState(false);

    // 접힘 상태는 localStorage에 남긴다(서버 렌더에는 없으므로 마운트 후 읽는다).
    useEffect(() => {
        try {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setCollapsed(window.localStorage.getItem(COLLAPSE_KEY) === "1");
        } catch {
            /* 저장소를 못 쓰면 펼친 상태로 둔다 */
        }
    }, []);

    const toggle = () => {
        setCollapsed(prev => {
            const next = !prev;
            try { window.localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0"); } catch { }
            return next;
        });
    };

    return (
        <HStack align="start" gap={0} minH="100vh" bg="bg.main">
            <Sidebar collapsed={collapsed} />

            {/* 좁은 화면에서 사이드바가 펼쳐지면 본문을 덮는 배경 (탭하면 닫힘) */}
            {!collapsed && (
                <Box
                    display={{ base: "block", md: "none" }}
                    position="fixed"
                    inset={0}
                    bg="blackAlpha.600"
                    zIndex={90}
                    onClick={toggle}
                />
            )}

            {/* 본문 = 상단 바(고정) + 스크롤 영역. 스크롤을 이 한 곳에만 두어
                페이지와 표가 각각 스크롤되는 이중 스크롤을 막는다. */}
            <Box flex="1" minW={0} h="100vh" display="flex" flexDirection="column" position="relative">
                {/* 상단 바 — 사이드바 밖·스크롤 영역 밖이라 항상 보인다 */}
                <HStack
                    flexShrink={0}
                    zIndex={20}
                    px={{ base: 4, lg: 6 }}
                    py={3}
                    gap={3}
                    bg="bg.main"
                    borderBottom="1px solid"
                    borderColor="border.subtle"
                >
                    <Box
                        as="button"
                        onClick={toggle}
                        display="flex"
                        alignItems="center"
                        gap={2}
                        px={3}
                        py={2}
                        borderRadius="lg"
                        borderWidth="1px"
                        borderColor="border.subtle"
                        bg="bg.panel"
                        color="fg.muted"
                        fontSize="xs"
                        fontWeight="bold"
                        cursor="pointer"
                        _hover={{ color: "accent.500", borderColor: "accent.500" }}
                        aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
                        title={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
                    >
                        <Icon as={collapsed ? PanelLeftOpen : PanelLeftClose} boxSize="4" />
                        <Text>{collapsed ? "메뉴 펼치기" : "메뉴 접기"}</Text>
                    </Box>
                </HStack>

                <Box flex="1" minH={0} overflowY="auto" position="relative">
                    {/* 은은한 배경 효과 */}
                    <Box
                        position="absolute"
                        top={0}
                        left={0}
                        right={0}
                        h="500px"
                        bgGradient="linear(to-b, accent.500/5, transparent)"
                        pointerEvents="none"
                    />
                    {/* h(=100%)여야 자식의 height:100%가 풀리지 않는다.
                        minH만 주면 이 박스의 높이가 auto가 되어, 대시보드처럼
                        "화면 한 장에 담고 표 안에서만 스크롤" 하는 레이아웃이 무너진다.
                        내용이 더 길어지면 넘친 만큼 바깥 스크롤 영역이 스크롤한다. */}
                    <Box position="relative" zIndex={1} h="100%">
                        {children}
                    </Box>
                </Box>
            </Box>
        </HStack>
    );
}
