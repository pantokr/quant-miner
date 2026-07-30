/**
 * 붙여넣은 표 텍스트(CSV / TSV) → 컬럼 + 행 파싱.
 *
 * 엑셀·구글시트에서 복사하면 탭 구분, /search의 CSV 내보내기는 쉼표 구분이므로
 * 구분자를 헤더 줄에서 추론한다. 따옴표로 감싼 필드와 이스케이프("")를 지원한다.
 */
export type CellValue = string | number | null;
export type TableRow = Record<string, CellValue>;

export interface TableColumn {
    key: string;
    /** 값의 대부분이 숫자로 읽히면 numeric — Y축 후보가 된다. */
    numeric: boolean;
}

export interface ParsedTable {
    columns: TableColumn[];
    rows: TableRow[];
    error?: string;
}

function detectDelimiter(headerLine: string): string {
    const tabs = (headerLine.match(/\t/g) || []).length;
    const commas = (headerLine.match(/,/g) || []).length;
    const semis = (headerLine.match(/;/g) || []).length;
    if (tabs >= commas && tabs >= semis && tabs > 0) return "\t";
    if (semis > commas) return ";";
    return ",";
}

/** 따옴표 안의 구분자·줄바꿈을 보존하며 한 줄을 자른다. */
function splitLine(line: string, delimiter: string): string[] {
    const out: string[] = [];
    let cur = "";
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (inQuotes) {
            if (ch === '"') {
                if (line[i + 1] === '"') { cur += '"'; i++; }
                else inQuotes = false;
            } else {
                cur += ch;
            }
        } else if (ch === '"') {
            inQuotes = true;
        } else if (ch === delimiter) {
            out.push(cur);
            cur = "";
        } else {
            cur += ch;
        }
    }
    out.push(cur);
    return out.map(s => s.trim());
}

/** 숫자 판정 — 천단위 쉼표, 백분율, 통화기호, 괄호 음수를 허용한다. */
export function toNumber(raw: unknown): number | null {
    if (raw === null || raw === undefined || raw === "") return null;
    if (typeof raw === "number") return Number.isFinite(raw) ? raw : null;
    if (typeof raw === "boolean") return null;

    let s = String(raw).trim();
    if (!s || s === "-") return null;

    let negative = false;
    if (/^\(.*\)$/.test(s)) { negative = true; s = s.slice(1, -1); }

    s = s.replace(/[,₩$€¥\s]/g, "").replace(/%$/, "");
    if (!/^[+-]?\d*\.?\d+(e[+-]?\d+)?$/i.test(s)) return null;

    const n = Number(s);
    if (!Number.isFinite(n)) return null;
    return negative ? -n : n;
}

export function parseTable(text: string): ParsedTable {
    const lines = text.replace(/\r\n?/g, "\n").split("\n").filter(l => l.trim() !== "");
    if (lines.length < 2) {
        return { columns: [], rows: [], error: "머리글 한 줄과 데이터 한 줄 이상이 필요합니다." };
    }

    const delimiter = detectDelimiter(lines[0]);
    const header = splitLine(lines[0], delimiter);
    if (header.length < 2) {
        return { columns: [], rows: [], error: "열이 하나뿐입니다. 구분자(쉼표/탭)를 확인하세요." };
    }

    // 빈 머리글·중복 머리글을 고유 키로 정리
    const seen = new Map<string, number>();
    const keys = header.map((h, i) => {
        const base = h || `열${i + 1}`;
        const count = seen.get(base) ?? 0;
        seen.set(base, count + 1);
        return count ? `${base}_${count + 1}` : base;
    });

    const rows: TableRow[] = [];
    for (let i = 1; i < lines.length; i++) {
        const cells = splitLine(lines[i], delimiter);
        const row: TableRow = {};
        keys.forEach((key, c) => {
            const cell = cells[c] ?? "";
            row[key] = cell === "" ? null : cell;
        });
        rows.push(row);
    }

    // 비어 있지 않은 값의 80% 이상이 숫자로 읽히면 숫자 컬럼으로 본다
    const columns: TableColumn[] = keys.map(key => {
        const values = rows.map(r => r[key]).filter(v => v !== null && v !== "");
        const numericCount = values.filter(v => toNumber(v) !== null).length;
        return { key, numeric: values.length > 0 && numericCount / values.length >= 0.8 };
    });

    return { columns, rows };
}

/** JSON 배열(객체 배열) → 같은 구조. /search에서 넘어온 데이터에 쓴다. */
export function fromRecords(records: Record<string, unknown>[]): ParsedTable {
    if (!records.length) return { columns: [], rows: [], error: "데이터가 비어 있습니다." };

    const keys: string[] = [];
    records.forEach(r => Object.keys(r).forEach(k => { if (!keys.includes(k)) keys.push(k); }));

    const rows: TableRow[] = records.map(r => {
        const row: TableRow = {};
        keys.forEach(k => {
            const v = r[k];
            row[k] = v === null || v === undefined ? null
                : typeof v === "number" ? v
                    : typeof v === "boolean" ? String(v)
                        : String(v);
        });
        return row;
    });

    const columns: TableColumn[] = keys.map(key => {
        const values = rows.map(r => r[key]).filter(v => v !== null && v !== "");
        const numericCount = values.filter(v => toNumber(v) !== null).length;
        return { key, numeric: values.length > 0 && numericCount / values.length >= 0.8 };
    });

    return { columns, rows };
}
