export type ColumnType = "text" | "number" | "price" | "percent" | "date" | "time" | "signed";

export interface GridColumn {
    key: string;
    label: string;
    type?: ColumnType;   // 기본 "text"
    width?: string;      // 예: "120px"
    /** 셀 원본값을 표시 문자열로 변환 (지정 시 type 포맷터보다 우선) */
    format?: (value: unknown, row: GridRow) => string;
}

export type GridRow = Record<string, unknown>;
