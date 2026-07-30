import { ColumnType, GridColumn, GridRow } from "./types";

/** 문자열/숫자 혼재(KIS 응답은 대부분 문자열)를 안전하게 숫자로. 실패 시 null. */
export function toNumber(value: unknown): number | null {
    if (value === null || value === undefined || value === "") return null;
    const n = typeof value === "number" ? value : Number(String(value).replace(/,/g, ""));
    return Number.isFinite(n) ? n : null;
}

function formatByType(value: unknown, type: ColumnType): string {
    if (value === null || value === undefined || value === "") return "-";

    switch (type) {
        case "number":
        case "price":
        case "signed": {
            const n = toNumber(value);
            if (n === null) return String(value);
            const sign = type === "signed" && n > 0 ? "+" : "";
            return sign + n.toLocaleString();
        }
        case "percent": {
            const n = toNumber(value);
            if (n === null) return String(value);
            return `${n > 0 ? "+" : ""}${n.toFixed(2)}%`;
        }
        case "date": {
            const s = String(value);
            if (s.length === 8) return `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}`;
            if (s.length === 6) return `${s.slice(0, 4)}-${s.slice(4, 6)}`;
            return s;
        }
        case "time": {
            const s = String(value).padStart(6, "0");
            return `${s.slice(0, 2)}:${s.slice(2, 4)}:${s.slice(4, 6)}`;
        }
        default:
            return String(value);
    }
}

export function formatCell(column: GridColumn, row: GridRow): string {
    const value = row[column.key];
    if (column.format) return column.format(value, row);
    return formatByType(value, column.type ?? "text");
}

/** 숫자형 컬럼은 숫자로, 나머지는 문자열로 비교. null은 항상 뒤로 보낸다. */
export function compareRows(a: GridRow, b: GridRow, column: GridColumn, desc: boolean): number {
    const numeric = column.type && column.type !== "text" && column.type !== "time";
    const av = a[column.key];
    const bv = b[column.key];

    let result: number;
    if (numeric) {
        const an = toNumber(av);
        const bn = toNumber(bv);
        if (an === null && bn === null) result = 0;
        else if (an === null) return 1;
        else if (bn === null) return -1;
        else result = an - bn;
    } else {
        result = String(av ?? "").localeCompare(String(bv ?? ""));
    }
    return desc ? -result : result;
}

/** 엑셀에서 바로 열리도록 BOM 포함 CSV 문자열 생성. */
export function toCsv(columns: GridColumn[], rows: GridRow[]): string {
    const escape = (s: string) => (/[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s);
    const header = columns.map(c => escape(c.label)).join(",");
    const body = rows.map(row =>
        columns.map(c => escape(String(row[c.key] ?? ""))).join(",")
    );
    return "﻿" + [header, ...body].join("\n");
}

export function downloadCsv(filename: string, csv: string) {
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}
