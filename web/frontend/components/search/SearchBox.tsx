"use client";

import { useEffect, useRef, useState } from "react";
import { Badge, Box, HStack, Icon, Input, Text, VStack } from "@chakra-ui/react";
import { Clock, Search, X } from "lucide-react";
import { MasterStock, isStockCode, searchStocks } from "@/lib/stock-search";

const RECENT_KEY = "quant-miner:recent-stocks";
const RECENT_MAX = 8;

export interface SelectedStock {
    code: string;
    name: string;
    market?: string;
}

function loadRecent(): SelectedStock[] {
    if (typeof window === "undefined") return [];
    try {
        const raw = window.localStorage.getItem(RECENT_KEY);
        const parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed.slice(0, RECENT_MAX) : [];
    } catch {
        return [];
    }
}

function saveRecent(list: SelectedStock[]) {
    try {
        window.localStorage.setItem(RECENT_KEY, JSON.stringify(list));
    } catch {
        // 프라이빗 모드 등 저장 불가 — 최근 검색 기능만 비활성화되고 조회는 정상 동작
    }
}

const toSelected = (s: MasterStock): SelectedStock => ({
    code: s.stock_code,
    name: s.name,
    market: s.market,
});

interface Props {
    selected: SelectedStock | null;
    onSelect: (stock: SelectedStock) => void;
}

export function SearchBox({ selected, onSelect }: Props) {
    const [query, setQuery] = useState("");
    const [open, setOpen] = useState(false);
    const [cursor, setCursor] = useState(0);
    const [recent, setRecent] = useState<SelectedStock[]>([]);
    const [result, setResult] = useState<{ query: string; rows: MasterStock[] }>({ query: "", rows: [] });
    const boxRef = useRef<HTMLDivElement>(null);

    // localStorage는 서버 렌더 시점에 없으므로 마운트 후에 읽는다(하이드레이션 불일치 방지).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    useEffect(() => setRecent(loadRecent()), []);

    // 바깥 클릭 시 제안 목록 닫기
    useEffect(() => {
        const onClickOutside = (e: MouseEvent) => {
            if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
        };
        document.addEventListener("mousedown", onClickOutside);
        return () => document.removeEventListener("mousedown", onClickOutside);
    }, []);

    // 서버 검색 — 입력이 멎은 뒤 200ms에 한 번만 요청하고, 이전 요청은 취소한다.
    // 결과에 검색어를 함께 담아 두고 "결과의 검색어 ≠ 현재 검색어"를 로딩으로 본다
    // (별도 loading state를 두면 effect 안에서 동기 setState가 필요해진다).
    const trimmed = query.trim();
    const suggestions = result.query === trimmed ? result.rows : [];
    const searching = trimmed.length > 0 && result.query !== trimmed;

    useEffect(() => {
        if (!trimmed) return;
        const controller = new AbortController();
        const timer = setTimeout(() => {
            searchStocks(trimmed, controller.signal)
                .then(rows => setResult({ query: trimmed, rows }))
                .catch(err => {
                    if (err?.name !== "AbortError") setResult({ query: trimmed, rows: [] });
                });
        }, 200);
        return () => { clearTimeout(timer); controller.abort(); };
    }, [trimmed]);

    const codeOnly =
        isStockCode(query) && !suggestions.some(s => s.stock_code === query.trim());

    const commit = (stock: SelectedStock) => {
        onSelect(stock);
        setQuery("");
        setOpen(false);
        setRecent(prev => {
            const next = [stock, ...prev.filter(s => s.code !== stock.code)].slice(0, RECENT_MAX);
            saveRecent(next);
            return next;
        });
    };

    /** 입력값 확정 — 목록에 없어도 6자리 코드면 그대로 조회한다. */
    const commitQuery = () => {
        const q = query.trim();
        if (!q) return;
        if (isStockCode(q)) {
            const known = suggestions.find(s => s.stock_code === q);
            commit(known ? toSelected(known) : { code: q, name: q });
            return;
        }
        if (suggestions.length) commit(toSelected(suggestions[Math.min(cursor, suggestions.length - 1)]));
    };

    const onKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter") { e.preventDefault(); commitQuery(); return; }
        if (e.key === "Escape") { setOpen(false); return; }
        if (!suggestions.length) return;
        if (e.key === "ArrowDown") { e.preventDefault(); setCursor(c => (c + 1) % suggestions.length); }
        if (e.key === "ArrowUp") { e.preventDefault(); setCursor(c => (c - 1 + suggestions.length) % suggestions.length); }
    };

    const clearRecent = () => {
        setRecent([]);
        saveRecent([]);
    };

    return (
        <VStack align="stretch" gap={3} ref={boxRef} position="relative">
            <HStack
                bg="bg.panel"
                borderWidth="1px"
                borderColor={open ? "accent.500" : "border.subtle"}
                borderRadius="2xl"
                px={5}
                py={1}
                boxShadow="xs"
                transition="border-color 0.15s"
            >
                <Icon as={Search} boxSize="5" color={open ? "accent.500" : "fg.muted"} />
                <Input
                    value={query}
                    onChange={e => { setQuery(e.target.value); setOpen(true); setCursor(0); }}
                    onFocus={() => setOpen(true)}
                    onKeyDown={onKeyDown}
                    placeholder="종목명 또는 6자리 종목코드 (예: 삼성전자, 005930)"
                    variant="flushed"
                    size="lg"
                    border="none"
                    fontWeight="bold"
                    _focusVisible={{ borderColor: "transparent", boxShadow: "none" }}
                />
                {selected && (
                    <Badge variant="subtle" colorPalette="accent" borderRadius="md" px={2} flexShrink={0}>
                        {selected.name} · {selected.code}
                    </Badge>
                )}
                <Box
                    as="button"
                    px={4} py={2}
                    my={2}
                    borderRadius="xl"
                    bg="accent.500"
                    color="white"
                    fontSize="sm"
                    fontWeight="bold"
                    flexShrink={0}
                    cursor="pointer"
                    _hover={{ bg: "accent.600" }}
                    onClick={commitQuery}
                >
                    조회
                </Box>
            </HStack>

            {/* 자동완성 */}
            {open && (query.trim().length > 0) && (
                <Box
                    position="absolute"
                    top="72px"
                    left={0}
                    right={0}
                    zIndex={20}
                    bg="bg.panel"
                    borderWidth="1px"
                    borderColor="border.subtle"
                    borderRadius="2xl"
                    boxShadow="lg"
                    overflow="hidden"
                    maxH="380px"
                    overflowY="auto"
                >
                    {codeOnly && (
                        <HStack
                            px={5} py={3}
                            cursor="pointer"
                            bg="accent.500/10"
                            _hover={{ bg: "accent.500/20" }}
                            onClick={() => commit({ code: query.trim(), name: query.trim() })}
                        >
                            <Icon as={Search} boxSize="4" color="accent.500" />
                            <Text fontSize="sm" fontWeight="bold" color="fg">
                                종목코드 {query.trim()} 직접 조회
                            </Text>
                        </HStack>
                    )}
                    {suggestions.map((s, i) => (
                        <HStack
                            key={s.stock_code}
                            px={5} py={3}
                            justify="space-between"
                            cursor="pointer"
                            bg={i === cursor ? "bg.muted" : "transparent"}
                            _hover={{ bg: "bg.muted" }}
                            onMouseEnter={() => setCursor(i)}
                            onClick={() => commit(toSelected(s))}
                        >
                            <HStack gap={3}>
                                <Text fontSize="sm" fontWeight="800" color="fg">{s.name}</Text>
                                <Text fontSize="xs" fontWeight="bold" color="fg.muted">{s.stock_code}</Text>
                            </HStack>
                            <HStack gap={2}>
                                <Badge
                                    size="sm"
                                    variant="subtle"
                                    colorPalette={s.market === "KOSPI" ? "blue" : "purple"}
                                    borderRadius="md"
                                >
                                    {s.market}
                                </Badge>
                            </HStack>
                        </HStack>
                    ))}
                    {!suggestions.length && !codeOnly && (
                        <Box px={5} py={6}>
                            <Text fontSize="sm" color="fg.subtle" fontWeight="medium">
                                {searching
                                    ? "검색 중..."
                                    : "일치하는 종목이 없습니다. 6자리 종목코드를 직접 입력해 보세요."}
                            </Text>
                        </Box>
                    )}
                </Box>
            )}

            {/* 최근 조회 */}
            {recent.length > 0 && (
                <HStack gap={2} flexWrap="wrap">
                    <HStack gap={1.5} color="fg.muted">
                        <Icon as={Clock} boxSize="3.5" />
                        <Text fontSize="2xs" fontWeight="black" letterSpacing="wider">RECENT</Text>
                    </HStack>
                    {recent.map(s => (
                        <Box
                            key={s.code}
                            as="button"
                            px={3} py={1}
                            borderRadius="lg"
                            borderWidth="1px"
                            borderColor={selected?.code === s.code ? "accent.500" : "border.subtle"}
                            bg={selected?.code === s.code ? "accent.500/10" : "bg.panel"}
                            fontSize="xs"
                            fontWeight="bold"
                            color={selected?.code === s.code ? "accent.500" : "fg.subtle"}
                            cursor="pointer"
                            _hover={{ borderColor: "accent.500", color: "accent.500" }}
                            onClick={() => onSelect(s)}
                        >
                            {s.name}
                        </Box>
                    ))}
                    <Box
                        as="button"
                        p={1}
                        borderRadius="md"
                        color="fg.muted"
                        cursor="pointer"
                        _hover={{ color: "red.500" }}
                        onClick={clearRecent}
                        title="최근 조회 지우기"
                    >
                        <Icon as={X} boxSize="3.5" />
                    </Box>
                </HStack>
            )}
        </VStack>
    );
}
