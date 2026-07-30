"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Box, HStack, Icon, Text, VStack } from "@chakra-ui/react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { DataGrid } from "@/components/datagrid/DataGrid";
import { hasNumericColumn, sendToVisualize } from "@/components/visualize/handoff";
import { DEFAULT_PARAMS, Dataset, QueryParams, daysAgo } from "./datasets";
import { OrderbookBoard } from "./OrderbookBoard";
import { QueryControls } from "./QueryControls";
import { SelectedStock } from "./SearchBox";
import { useDataset } from "./useDataset";

/** 데이터셋마다 권장 조회 기간이 다르므로 진입 시 기본값을 맞춰 준다. */
function initParams(dataset: Dataset): QueryParams {
    return dataset.defaultRangeDays
        ? { ...DEFAULT_PARAMS, start: daysAgo(dataset.defaultRangeDays) }
        : { ...DEFAULT_PARAMS };
}

interface Props {
    dataset: Dataset;
    stock: SelectedStock;
}

export function DatasetPanel({ dataset, stock }: Props) {
    // 호가는 표보다 가격 사다리가 훨씬 읽기 쉬우므로 전용 뷰를 쓴다.
    if (dataset.id === "orderbook") {
        return (
            <VStack align="stretch" gap={4}>
                <VStack align="start" gap={0.5}>
                    <Text fontSize="sm" fontWeight="900" color="fg">{dataset.label}</Text>
                    <Text fontSize="xs" color="fg.subtle" fontWeight="medium">{dataset.description}</Text>
                </VStack>
                <OrderbookBoard stock={stock} />
            </VStack>
        );
    }
    return <GridPanel dataset={dataset} stock={stock} />;
}


function GridPanel({ dataset, stock }: Props) {
    // 편집 중인 조건(params)과 실제 요청에 쓰인 조건(applied)을 분리한다.
    // 전 기간 수집처럼 무거운 조회가 입력 도중에 발사되지 않도록 하기 위함.
    //
    // 종목이나 데이터셋이 바뀌면 부모가 key로 이 컴포넌트를 다시 마운트하므로
    // (app/search/page.tsx의 `key={stock.code}:${dataset.id}`) 조건 초기화는 여기서 하지 않는다.
    const [params, setParams] = useState<QueryParams>(() => initParams(dataset));
    const [applied, setApplied] = useState<QueryParams>(() => initParams(dataset));
    const [reloadKey, setReloadKey] = useState(0);
    const [handoffNote, setHandoffNote] = useState("");
    const router = useRouter();

    const baseUrl = dataset.buildUrl(stock.code, applied);
    // 같은 조건으로 다시 조회할 때 useDataset이 URL 변화를 감지하도록 캐시 버스터를 붙인다.
    const url = reloadKey
        ? `${baseUrl}${baseUrl.includes("?") ? "&" : "?"}_r=${reloadKey}`
        : baseUrl;
    const { data, loading, error, fetchedAt } = useDataset(url);

    const rows = useMemo(() => {
        if (data === null || data === undefined) return [];
        try {
            return dataset.extract(data, applied);
        } catch {
            return [];
        }
    }, [data, dataset, applied]);

    const columns = useMemo(() => dataset.columns(rows, applied), [dataset, rows, applied]);

    const dirty = JSON.stringify(params) !== JSON.stringify(applied);

    return (
        <VStack align="stretch" gap={4}>
            <HStack justify="space-between" align="start" flexWrap="wrap" gap={3}>
                <VStack align="start" gap={0.5}>
                    <Text fontSize="sm" fontWeight="900" color="fg">{dataset.label}</Text>
                    <Text fontSize="xs" color="fg.subtle" fontWeight="medium">{dataset.description}</Text>
                </VStack>

                <HStack gap={3} flexWrap="wrap">
                    <QueryControls
                        controls={dataset.controls}
                        params={params}
                        onChange={patch => setParams(p => ({ ...p, ...patch }))}
                    />
                    <Box
                        as="button"
                        px={4} py={1.5}
                        borderRadius="lg"
                        bg={dirty ? "accent.500" : "bg.muted"}
                        color={dirty ? "white" : "fg.muted"}
                        borderWidth="1px"
                        borderColor={dirty ? "accent.500" : "border.subtle"}
                        fontSize="xs"
                        fontWeight="bold"
                        cursor="pointer"
                        _hover={{ borderColor: "accent.500", color: dirty ? "white" : "accent.500" }}
                        onClick={() => {
                            if (dirty) setApplied(params);
                            else setReloadKey(k => k + 1);
                        }}
                    >
                        <HStack gap={1.5}>
                            <Icon as={RefreshCw} boxSize="3.5" />
                            <Text>{dirty ? "조건 적용" : "새로고침"}</Text>
                        </HStack>
                    </Box>
                </HStack>
            </HStack>

            {dataset.warning && (
                <HStack
                    gap={2}
                    bg="orange.500/10"
                    borderWidth="1px"
                    borderColor="orange.500/30"
                    borderRadius="xl"
                    px={4} py={2.5}
                >
                    <Icon as={AlertTriangle} boxSize="3.5" color="orange.500" flexShrink={0} />
                    <Text fontSize="xs" fontWeight="medium" color="fg.subtle">{dataset.warning}</Text>
                </HStack>
            )}

            {handoffNote && (
                <HStack
                    gap={2}
                    bg="orange.500/10"
                    borderWidth="1px"
                    borderColor="orange.500/30"
                    borderRadius="xl"
                    px={4} py={2.5}
                >
                    <Icon as={AlertTriangle} boxSize="3.5" color="orange.500" flexShrink={0} />
                    <Text fontSize="xs" fontWeight="medium" color="fg.subtle">{handoffNote}</Text>
                </HStack>
            )}

            <DataGrid
                columns={columns}
                rows={rows}
                loading={loading}
                error={error}
                exportName={`${stock.code}_${dataset.id}`}
                emptyMessage="조회된 데이터가 없습니다. 조회 조건을 바꾸거나 다른 기간을 선택해 보세요."
                onVisualize={visible => {
                    // 정렬·필터가 적용된, 지금 보이는 행을 그대로 넘긴다
                    const result = sendToVisualize(`${stock.name} · ${dataset.label}`, visible);
                    if (!result.ok) {
                        setHandoffNote(result.error ?? "그래프로 넘기지 못했습니다.");
                        return;
                    }
                    router.push("/visualize");
                }}
                visualizeDisabledReason={
                    rows.length && !hasNumericColumn(rows)
                        ? "숫자 열이 없어 그래프로 그릴 수 없는 표입니다."
                        : undefined
                }
                toolbar={
                    fetchedAt && !loading ? (
                        <Text fontSize="2xs" fontWeight="bold" color="fg.muted" letterSpacing="wider">
                            {fetchedAt.toLocaleTimeString("ko-KR")} 조회
                        </Text>
                    ) : null
                }
            />
        </VStack>
    );
}
