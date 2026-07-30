"use client";

import { HStack, Icon, Text } from "@chakra-ui/react";
import { CalendarRange } from "lucide-react";
import { ControlKey, FINANCE_TYPES, PERIOD_OPTIONS, QueryParams } from "./datasets";

/** YYYYMMDD ↔ <input type="date">의 YYYY-MM-DD 변환 */
const toInput = (ymd: string) => `${ymd.slice(0, 4)}-${ymd.slice(4, 6)}-${ymd.slice(6, 8)}`;
const fromInput = (value: string) => value.replace(/-/g, "");

const selectStyle: React.CSSProperties = {
    padding: "6px 12px",
    borderRadius: "10px",
    border: "1px solid var(--chakra-colors-border-subtle)",
    fontSize: "12px",
    fontWeight: 700,
    outline: "none",
    backgroundColor: "var(--chakra-colors-bg-panel)",
    color: "var(--chakra-colors-fg)",
    cursor: "pointer",
};

const dateStyle: React.CSSProperties = { ...selectStyle, fontWeight: 600 };

interface Props {
    controls: ControlKey[];
    params: QueryParams;
    onChange: (patch: Partial<QueryParams>) => void;
}

export function QueryControls({ controls, params, onChange }: Props) {
    if (!controls.length) return null;

    const rangeDisabled = params.allHistory && controls.includes("allHistory");

    return (
        <HStack gap={3} flexWrap="wrap">
            {controls.includes("financeType") && (
                <select
                    value={params.financeType}
                    onChange={e => onChange({ financeType: e.target.value })}
                    style={selectStyle}
                >
                    {FINANCE_TYPES.map(t => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                </select>
            )}

            {controls.includes("periodType") && (
                <select
                    value={params.periodType}
                    onChange={e => onChange({ periodType: e.target.value as QueryParams["periodType"] })}
                    style={selectStyle}
                >
                    <option value="A">연간</option>
                    <option value="Q">분기</option>
                </select>
            )}

            {controls.includes("period") && (
                <select
                    value={params.period}
                    onChange={e => onChange({ period: e.target.value as QueryParams["period"] })}
                    style={selectStyle}
                >
                    {PERIOD_OPTIONS.map(p => (
                        <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                </select>
            )}

            {controls.includes("dateRange") && (
                <HStack gap={2} opacity={rangeDisabled ? 0.4 : 1}>
                    <Icon as={CalendarRange} boxSize="3.5" color="fg.muted" />
                    <input
                        type="date"
                        value={toInput(params.start)}
                        disabled={rangeDisabled}
                        onChange={e => onChange({ start: fromInput(e.target.value) })}
                        style={dateStyle}
                    />
                    <Text fontSize="xs" color="fg.muted" fontWeight="bold">~</Text>
                    <input
                        type="date"
                        value={toInput(params.end)}
                        disabled={rangeDisabled}
                        onChange={e => onChange({ end: fromInput(e.target.value) })}
                        style={dateStyle}
                    />
                </HStack>
            )}

            {controls.includes("allHistory") && (
                <label style={{ fontSize: 12, fontWeight: 700, cursor: "pointer", color: "var(--chakra-colors-fg-subtle)" }}>
                    <input
                        type="checkbox"
                        checked={params.allHistory}
                        onChange={e => onChange({ allHistory: e.target.checked })}
                        style={{ marginRight: 6, cursor: "pointer" }}
                    />
                    전 기간
                </label>
            )}
        </HStack>
    );
}
