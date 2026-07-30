"use client";

/**
 * 캔들(봉) 도형 — Recharts에는 캔들차트가 없어 Bar의 custom shape로 그린다.
 *
 * 쓰는 쪽에서 각 데이터 포인트에 `_range: [low, high]`를 넣고 Bar의 dataKey로 지정하면,
 * Recharts가 저·고가를 잇는 "떠 있는 막대"로 y/height를 계산해 준다. 그 픽셀 좌표를
 * 받아 심지(high~low)와 몸통(open~close)을 다시 그린다.
 *
 * 색은 한국 관행대로 상승 빨강 / 하락 파랑. 보합은 회색.
 */
export interface CandleDatum {
    open: number;
    high: number;
    low: number;
    close: number;
    _range: [number, number];
    [key: string]: unknown;
}

export const CANDLE_UP = "#e34948";
export const CANDLE_DOWN = "#2a78d6";
export const CANDLE_FLAT = "#898781";

export function candleColor(open: number, close: number): string {
    if (close > open) return CANDLE_UP;
    if (close < open) return CANDLE_DOWN;
    return CANDLE_FLAT;
}

interface ShapeProps {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
    payload?: CandleDatum;
}

export function CandleShape(props: ShapeProps) {
    const { x = 0, y = 0, width = 0, height = 0, payload } = props;
    if (!payload) return null;

    const { open, high, low, close } = payload;
    if ([open, high, low, close].some(v => typeof v !== "number" || !Number.isFinite(v))) {
        return null;
    }

    const span = high - low;
    // 고가=저가(가격 변동 없음)면 픽셀 환산이 불가하므로 얇은 선 하나로 표시
    const ratio = span > 0 ? height / span : 0;

    const bodyTopValue = Math.max(open, close);
    const bodyBottomValue = Math.min(open, close);
    const bodyY = span > 0 ? y + (high - bodyTopValue) * ratio : y + height / 2;
    const bodyH = span > 0 ? Math.max(1, (bodyTopValue - bodyBottomValue) * ratio) : 1;

    const color = candleColor(open, close);
    // 봉이 너무 얇아지면 심지가 안 보이므로 몸통 폭에 하한을 둔다
    const bodyW = Math.max(1, Math.min(width, width * 0.7));
    const bodyX = x + (width - bodyW) / 2;
    const centerX = x + width / 2;

    return (
        <g>
            {/* 심지 (고가 ~ 저가) */}
            <line
                x1={centerX} x2={centerX}
                y1={y} y2={y + height}
                stroke={color}
                strokeWidth={1}
            />
            {/* 몸통 (시가 ~ 종가) */}
            <rect
                x={bodyX} y={bodyY}
                width={bodyW} height={bodyH}
                fill={color}
                stroke={color}
            />
        </g>
    );
}

/** 캔들 툴팁 본문 — 시/고/저/종가를 한 번에 보여 준다. */
export function CandleTooltip({
    active, payload, label, labelFormatter, surface, grid, text,
}: {
    active?: boolean;
    // Recharts가 readonly 배열로 넘겨주므로 느슨하게 받는다
    payload?: readonly { payload?: unknown }[];
    label?: unknown;
    labelFormatter?: (v: unknown) => string;
    surface: string;
    grid: string;
    text: string;
}) {
    if (!active || !payload?.length) return null;
    const d = payload[0]?.payload as CandleDatum | undefined;
    if (!d || typeof d.open !== "number") return null;
    const color = candleColor(d.open, d.close);
    const diff = d.close - d.open;
    const rate = d.open ? (diff / d.open) * 100 : 0;

    const row = (name: string, value: number) => (
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
            <span style={{ opacity: 0.7 }}>{name}</span>
            <span style={{ fontVariantNumeric: "tabular-nums" }}>{value.toLocaleString()}</span>
        </div>
    );

    return (
        <div
            style={{
                borderRadius: 10,
                border: `1px solid ${grid}`,
                background: surface,
                color: text,
                fontSize: 12,
                fontWeight: 600,
                padding: "8px 10px",
                boxShadow: "0 10px 15px -3px rgba(0,0,0,0.12)",
                minWidth: 132,
            }}
        >
            <div style={{ marginBottom: 6, opacity: 0.8 }}>
                {labelFormatter ? labelFormatter(label) : String(label ?? "")}
            </div>
            {row("시가", d.open)}
            {row("고가", d.high)}
            {row("저가", d.low)}
            {row("종가", d.close)}
            <div style={{ marginTop: 4, color, fontWeight: 800 }}>
                {diff > 0 ? "+" : ""}{diff.toLocaleString()} ({rate > 0 ? "+" : ""}{rate.toFixed(2)}%)
            </div>
        </div>
    );
}
