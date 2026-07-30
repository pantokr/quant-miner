"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
    Box, Grid, HStack, Heading, Icon, Text, Textarea, VStack,
} from "@chakra-ui/react";
import {
    AreaChart, BarChart3, CandlestickChart, LineChart, ScatterChart, Table2, Trash2,
} from "lucide-react";
import { ChartCanvas, ChartKind, OhlcKeys } from "@/components/visualize/ChartCanvas";
import { ParsedTable, fromRecords, parseTable } from "@/components/visualize/parseTable";
import { HANDOFF_KEY } from "@/components/visualize/handoff";
import { DataGrid } from "@/components/datagrid/DataGrid";
import { GridColumn } from "@/components/datagrid/types";
import { MAX_SERIES, MAX_SERIES_ALL_PAIRS } from "@/lib/viz-palette";

const EMPTY: ParsedTable = { columns: [], rows: [] };

/** X축 후보로 어울리는 열 이름 (일자·시각·기간·결산년월) */
const AXIS_LIKE = /(^|_)(date|time|dt|period|yymm|일자|시각|기간|단계|결산)|stac_yymm/i;
/** 숫자로 읽히지만 값이 아닌 식별자 열 — Y축 기본 선택에서 제외 */
const ID_LIKE = /(^|_)(code|no|id|종목코드)$|^stock_code$|^sht_cd$/i;

const SAMPLE = `일자,종가,거래량
20260721,265000,18420111
20260722,258500,15233402
20260723,261000,12980551
20260724,254000,23296044
20260727,254000,19884120
20260728,220000,41639623
20260729,208500,65555523`;

const KINDS: { value: ChartKind; label: string; icon: typeof LineChart; hint: string }[] = [
    { value: "line", label: "선", icon: LineChart, hint: "시간에 따른 추세" },
    { value: "candle", label: "캔들", icon: CandlestickChart, hint: "시·고·저·종가를 한 봉으로 (상승 빨강 / 하락 파랑)" },
    { value: "area", label: "영역", icon: AreaChart, hint: "단일 시리즈 추세" },
    { value: "bar", label: "막대", icon: BarChart3, hint: "항목 간 크기 비교" },
    { value: "scatter", label: "산점도", icon: ScatterChart, hint: "두 값의 관계" },
];

/** 캔들용 O/H/L/C 열 자동 인식 — KIS 응답의 여러 표기를 함께 본다. */
const OHLC_PATTERNS: Record<keyof OhlcKeys, RegExp> = {
    open: /^(open|open_price|시가|stck_oprc|oprc)$/i,
    high: /^(high|high_price|고가|stck_hgpr|hgpr)$/i,
    low: /^(low|low_price|저가|stck_lwpr|lwpr)$/i,
    close: /^(close|close_price|종가|stck_clpr|clpr|stck_prpr)$/i,
};

function detectOhlc(columns: { key: string }[]): OhlcKeys | null {
    const found: Partial<OhlcKeys> = {};
    (Object.keys(OHLC_PATTERNS) as (keyof OhlcKeys)[]).forEach(role => {
        const hit = columns.find(c => OHLC_PATTERNS[role].test(c.key));
        if (hit) found[role] = hit.key;
    });
    return found.open && found.high && found.low && found.close
        ? (found as OhlcKeys)
        : null;
}

function Chip({
    active, onClick, children, disabled,
}: {
    active: boolean; onClick: () => void; children: React.ReactNode; disabled?: boolean;
}) {
    return (
        <Box
            as="button"
            px={3} py={1.5}
            borderRadius="lg"
            borderWidth="1px"
            borderColor={active ? "accent.500" : "border.subtle"}
            bg={active ? "accent.500" : "bg.panel"}
            color={active ? "white" : disabled ? "fg.muted" : "fg.subtle"}
            fontSize="xs"
            fontWeight="bold"
            cursor={disabled ? "not-allowed" : "pointer"}
            opacity={disabled ? 0.4 : 1}
            transition="all 0.15s"
            _hover={disabled || active ? undefined : { borderColor: "accent.500", color: "accent.500" }}
            onClick={() => { if (!disabled) onClick(); }}
        >
            {children}
        </Box>
    );
}

export default function VisualizePage() {
    const [raw, setRaw] = useState("");
    const [table, setTable] = useState<ParsedTable>(EMPTY);
    const [kind, setKind] = useState<ChartKind>("line");
    const [xKey, setXKey] = useState("");
    const [yKeys, setYKeys] = useState<string[]>([]);
    const [sortByValue, setSortByValue] = useState(false);
    const [source, setSource] = useState("");

    /** 파싱 결과를 싣고 X/Y 기본 선택을 잡는다. */
    const apply = useCallback((parsed: ParsedTable, label: string) => {
        setTable(parsed);
        setSource(label);
        if (parsed.error || !parsed.columns.length) {
            setXKey(""); setYKeys([]);
            return;
        }
        // X축: 날짜·시각처럼 보이는 열을 먼저 본다. 분봉의 trade_date처럼 숫자로 읽히는
        // 열도 있으므로 "비숫자 열"만으로는 부족하다.
        // 후보가 여럿이면 서로 다른 값이 가장 많은 쪽 — 분봉이면 trade_date(2개)가 아니라
        // trade_time(수백 개)이 가로축이 되어야 한다.
        const distinct = (key: string) => new Set(parsed.rows.map(r => r[key])).size;
        const axisLike = parsed.columns.filter(c => AXIS_LIKE.test(c.key));
        const x =
            (axisLike.length
                ? axisLike.reduce((best, c) => (distinct(c.key) > distinct(best.key) ? c : best))
                : undefined) ??
            parsed.columns.find(c => !c.numeric) ??
            parsed.columns[0];

        // Y축: 종목코드처럼 숫자지만 값이 아닌 열은 기본 선택에서 뺀다.
        const ys = parsed.columns
            .filter(c => c.numeric && c.key !== x.key && !ID_LIKE.test(c.key) && !AXIS_LIKE.test(c.key))
            .slice(0, 2);

        setXKey(x.key);
        setYKeys(ys.map(c => c.key));
    }, []);

    // /search 에서 넘어온 데이터가 있으면 그것부터 싣는다.
    // sessionStorage는 서버 렌더 시점에 없으므로 마운트 후에 읽는다(하이드레이션 불일치 방지).
    useEffect(() => {
        try {
            const stored = sessionStorage.getItem(HANDOFF_KEY);
            if (!stored) return;
            sessionStorage.removeItem(HANDOFF_KEY);
            const payload = JSON.parse(stored) as { label?: string; rows?: Record<string, unknown>[] };
            if (payload.rows?.length) {
                // eslint-disable-next-line react-hooks/set-state-in-effect
                apply(fromRecords(payload.rows), payload.label ?? "");
            }
        } catch {
            /* 넘겨받은 값이 깨졌으면 무시하고 빈 화면에서 시작 */
        }
    }, [apply]);

    const load = (text: string, label: string) => {
        setRaw(text);
        apply(parseTable(text), label);
    };

    const clear = () => {
        setRaw(""); setTable(EMPTY); setXKey(""); setYKeys([]); setSource("");
    };

    const seriesCap = kind === "scatter" ? MAX_SERIES_ALL_PAIRS : MAX_SERIES;
    // 산점도로 바꾸면 상한이 3으로 줄어든다 — 선택을 지우지 않고 그릴 때만 잘라 낸다.
    // (선 차트로 돌아오면 원래 고른 시리즈가 그대로 살아난다)
    const activeY = yKeys.slice(0, seriesCap);
    const atCap = activeY.length >= seriesCap;

    const toggleY = (key: string) => {
        setYKeys(prev =>
            prev.includes(key) ? prev.filter(k => k !== key)
                : prev.length >= seriesCap ? prev
                    : [...prev, key],
        );
    };

    const gridColumns = useMemo<GridColumn[]>(
        () => table.columns.map(c => ({
            key: c.key,
            label: c.key,
            type: c.numeric ? "number" : "text",
        })),
        [table.columns],
    );

    const numericColumns = table.columns.filter(c => c.numeric);
    const ohlc = useMemo(() => detectOhlc(table.columns), [table.columns]);

    return (
        <Box p={{ base: 6, lg: 10 }} bg="bg.main" minH="100%">
            <VStack align="start" mb={8} gap={2}>
                <HStack gap={3}>
                    <Box p={2} bg="accent.500" borderRadius="lg" color="white">
                        <BarChart3 size={24} />
                    </Box>
                    <Heading size="2xl" fontWeight="900" color="fg" letterSpacing="tight">
                        데이터 시각화
                    </Heading>
                </HStack>
                <Text fontSize="md" fontWeight="medium" color="fg.subtle">
                    표를 붙여넣거나 종목 조회 결과를 보내면 그래프로 그립니다
                </Text>
            </VStack>

            <VStack align="stretch" gap={6}>
                {/* 데이터 투입 */}
                <Box bg="bg.panel" borderRadius="2xl" borderWidth="1px" borderColor="border.subtle" p={6} boxShadow="xs">
                    <HStack justify="space-between" align="center" mb={3} flexWrap="wrap" gap={3}>
                        <VStack align="start" gap={0.5}>
                            <Text fontSize="sm" fontWeight="900" color="fg">데이터 붙여넣기</Text>
                            <Text fontSize="xs" color="fg.subtle" fontWeight="medium">
                                CSV·TSV 모두 인식합니다. 엑셀에서 복사한 표를 그대로 붙여넣어도 됩니다.
                            </Text>
                        </VStack>
                        <HStack gap={2}>
                            <Chip active={false} onClick={() => load(SAMPLE, "예시 데이터")}>예시 넣기</Chip>
                            <Chip active={false} onClick={clear}>
                                <HStack gap={1}><Icon as={Trash2} boxSize="3" /><Text>비우기</Text></HStack>
                            </Chip>
                        </HStack>
                    </HStack>

                    <Textarea
                        value={raw}
                        onChange={e => load(e.target.value, "붙여넣은 데이터")}
                        placeholder={"일자,종가,거래량\n20260729,208500,65555523\n..."}
                        rows={6}
                        fontFamily="mono"
                        fontSize="xs"
                        bg="bg.muted"
                        borderColor="border.subtle"
                        _focusVisible={{ borderColor: "accent.500", boxShadow: "none" }}
                    />

                    {table.error && (
                        <Text fontSize="xs" color="red.500" fontWeight="bold" mt={2}>{table.error}</Text>
                    )}
                    {!table.error && table.rows.length > 0 && (
                        <Text fontSize="xs" color="fg.muted" fontWeight="bold" mt={2}>
                            {source && `${source} · `}{table.rows.length.toLocaleString()}행 ·
                            {" "}{table.columns.length}열 (숫자 열 {numericColumns.length}개)
                        </Text>
                    )}
                </Box>

                {table.rows.length > 0 && !table.error && (
                    <>
                        {/* 축·차트 설정 */}
                        <Box bg="bg.panel" borderRadius="2xl" borderWidth="1px" borderColor="border.subtle" p={6} boxShadow="xs">
                            <Grid templateColumns={{ base: "1fr", lg: "auto 1fr" }} gap={6}>
                                <VStack align="start" gap={2}>
                                    <Text fontSize="2xs" fontWeight="black" color="fg.muted" letterSpacing="wider">
                                        차트 종류
                                    </Text>
                                    <HStack gap={2} flexWrap="wrap">
                                        {KINDS.map(k => {
                                            // 캔들은 O/H/L/C 열이 다 있어야 그릴 수 있다
                                            const blocked = k.value === "candle" && !ohlc;
                                            return (
                                                <Chip
                                                    key={k.value}
                                                    active={kind === k.value}
                                                    disabled={blocked}
                                                    onClick={() => setKind(k.value)}
                                                >
                                                    <HStack gap={1.5}>
                                                        <Icon as={k.icon} boxSize="3.5" />
                                                        <Text>{k.label}</Text>
                                                    </HStack>
                                                </Chip>
                                            );
                                        })}
                                    </HStack>
                                    <Text fontSize="2xs" color="fg.subtle" fontWeight="medium">
                                        {kind === "candle" && ohlc
                                            ? `${ohlc.open} · ${ohlc.high} · ${ohlc.low} · ${ohlc.close}`
                                            : KINDS.find(k => k.value === kind)?.hint}
                                    </Text>
                                    {!ohlc && (
                                        <Text fontSize="2xs" color="fg.muted" fontWeight="medium">
                                            캔들은 시·고·저·종가 열이 있는 표(일별 시세·분봉)에서 쓸 수 있습니다.
                                        </Text>
                                    )}
                                </VStack>

                                <VStack align="stretch" gap={4}>
                                    <VStack align="start" gap={2}>
                                        <Text fontSize="2xs" fontWeight="black" color="fg.muted" letterSpacing="wider">
                                            X축 (가로)
                                        </Text>
                                        <HStack gap={2} flexWrap="wrap">
                                            {table.columns.map(c => (
                                                <Chip key={c.key} active={xKey === c.key} onClick={() => setXKey(c.key)}>
                                                    {c.key}
                                                </Chip>
                                            ))}
                                        </HStack>
                                    </VStack>

                                    {/* 캔들은 O/H/L/C를 자동으로 쓰므로 Y축 선택이 필요 없다 */}
                                    <VStack align="start" gap={2} display={kind === "candle" ? "none" : "flex"}>
                                        <HStack gap={2} flexWrap="wrap">
                                            <Text fontSize="2xs" fontWeight="black" color="fg.muted" letterSpacing="wider">
                                                Y축 (세로 · 숫자 열)
                                            </Text>
                                            <Text fontSize="2xs" fontWeight="bold" color={atCap ? "orange.500" : "fg.subtle"}>
                                                {activeY.length} / {seriesCap}
                                                {kind === "scatter" && " · 산점도는 3개까지"}
                                            </Text>
                                        </HStack>
                                        <HStack gap={2} flexWrap="wrap">
                                            {numericColumns.map(c => {
                                                const on = activeY.includes(c.key);
                                                return (
                                                    <Chip
                                                        key={c.key}
                                                        active={on}
                                                        disabled={!on && atCap}
                                                        onClick={() => toggleY(c.key)}
                                                    >
                                                        {c.key}
                                                    </Chip>
                                                );
                                            })}
                                        </HStack>
                                        {atCap && (
                                            <Text fontSize="2xs" color="orange.500" fontWeight="bold">
                                                색만으로 구분할 수 있는 한도입니다. 더 보려면 차트를 나눠 그리세요.
                                            </Text>
                                        )}
                                    </VStack>

                                    {kind === "bar" && (
                                        <HStack gap={2}>
                                            <Chip active={sortByValue} onClick={() => setSortByValue(v => !v)}>
                                                값 큰 순 정렬
                                            </Chip>
                                        </HStack>
                                    )}
                                </VStack>
                            </Grid>
                        </Box>

                        {/* 차트 */}
                        <Box bg="bg.panel" borderRadius="2xl" borderWidth="1px" borderColor="border.subtle" p={6} boxShadow="xs">
                            <Text fontSize="sm" fontWeight="900" color="fg" mb={1}>
                                {kind === "candle"
                                    ? "시가 · 고가 · 저가 · 종가"
                                    : activeY.length ? activeY.join(" · ") : "그래프"}
                            </Text>
                            <Text fontSize="xs" color="fg.subtle" fontWeight="medium" mb={4}>
                                {xKey && `${xKey} 기준`}
                            </Text>
                            <ChartCanvas
                                kind={kind}
                                rows={table.rows}
                                xKey={xKey}
                                yKeys={activeY}
                                sortByValue={sortByValue}
                                ohlc={ohlc}
                            />
                        </Box>

                        {/* 원본 표 — 색 대비가 낮은 슬롯을 쓰는 라이트 모드의 보완 수단 */}
                        <Box bg="bg.panel" borderRadius="2xl" borderWidth="1px" borderColor="border.subtle" p={6} boxShadow="xs">
                            <HStack gap={2} mb={4}>
                                <Icon as={Table2} boxSize="4" color="fg.muted" />
                                <Text fontSize="sm" fontWeight="900" color="fg">원본 표</Text>
                            </HStack>
                            <DataGrid
                                columns={gridColumns}
                                rows={table.rows}
                                exportName="visualize"
                            />
                        </Box>
                    </>
                )}
            </VStack>
        </Box>
    );
}
