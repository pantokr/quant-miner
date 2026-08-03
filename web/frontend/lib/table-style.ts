/**
 * 표 공통 스타일 — 선을 줄이고 여백·정렬로 읽게 한다.
 *
 * 예전 표는 머리글에 회색 배경과 굵은 테두리가 깔리고, 행마다 실선이 그어지고,
 * 셀 글자는 black(900)이었다. 셋이 겹쳐 표 한 장이 카드처럼 무겁게 읽혔다.
 * 여기서는 선을 머리글 아래 하나와 행 사이 헤어라인으로 줄이고, 굵기는 두 단계
 * (머리글 bold / 값 medium)만 쓴다. 강조는 굵기가 아니라 색이 맡는다.
 *
 * 쓰는 법: Chakra Table의 각 조각에 그대로 펼친다.
 *   <Table.Row {...TABLE_HEADER_ROW}>
 *     <Table.ColumnHeader {...TABLE_HEADER_CELL}>…
 *   <Table.Row {...TABLE_ROW}>
 *     <Table.Cell {...TABLE_CELL}>…  /  <Table.Cell {...TABLE_NUM_CELL}>…
 */

/** 머리글 줄 — 회색 띠를 걷는다. 구분은 아래 실선 하나로 충분하다. */
export const TABLE_HEADER_ROW = {
    bg: "transparent",
} as const;

export const TABLE_HEADER_CELL = {
    // 판과 같은 색을 깐다 — 띠로 보이지 않으면서 stickyHeader일 때 행이 글자 뒤로 비쳐 지나가지 않는다
    bg: "bg.panel",
    py: 2.5,
    fontSize: "2xs",
    fontWeight: "bold",
    color: "fg.muted",
    letterSpacing: "wider",
    whiteSpace: "nowrap",
    borderBottomWidth: "1px",
    borderColor: "border.subtle",
} as const;

/** 본문 줄 — 행 사이는 헤어라인 하나. 짚는 자리는 hover가 알려 준다. */
export const TABLE_ROW = {
    _hover: { bg: "bg.muted" },
    transition: "background-color 0.12s",
} as const;

export const TABLE_CELL = {
    py: 2.5,
    fontSize: "xs",
    fontWeight: "medium",
    color: "fg",
    borderColor: "border.subtle",
    whiteSpace: "nowrap",
} as const;

/** 숫자 셀 — 오른쪽 맞춤 + 등폭 숫자. 자릿수가 세로로 맞아야 크기가 눈에 들어온다. */
export const TABLE_NUM_CELL = {
    ...TABLE_CELL,
    textAlign: "right",
    fontVariantNumeric: "tabular-nums",
} as const;

/** 표를 감싸는 판 — 테두리 하나만 두고 그림자는 걷는다 */
export const TABLE_SURFACE = {
    bg: "bg.panel",
    borderRadius: "xl",
    borderWidth: "1px",
    borderColor: "border.subtle",
    overflow: "hidden",
} as const;
