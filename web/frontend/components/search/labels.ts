/**
 * KIS 원본 응답 필드(영문 약어) → 한글 라벨.
 *
 * 재무제표·종목기본정보는 KIS가 raw dict를 그대로 내려주므로, 알려진 키만 한글로 바꾸고
 * 모르는 키는 원본 키를 그대로 노출한다(스키마가 바뀌어도 데이터가 사라지지 않도록).
 */
export const FINANCE_LABELS: Record<string, string> = {
    stac_yymm: "결산년월",

    // 재무상태표
    cras: "유동자산",
    fxas: "고정자산",
    total_aset: "자산총계",
    flow_lblt: "유동부채",
    fix_lblt: "고정부채",
    total_lblt: "부채총계",
    cpfn: "자본금",
    cfp_surp: "자본잉여금",
    prfi_surp: "이익잉여금",
    total_cptl: "자본총계",

    // 손익계산서
    sale_account: "매출액",
    sale_cost: "매출원가",
    sale_totl_prfi: "매출총이익",
    depr_cost: "감가상각비",
    sell_mang: "판매비와관리비",
    bsop_prti: "영업이익",
    bsop_non_ernn: "영업외수익",
    bsop_non_expn: "영업외비용",
    op_prfi: "경상이익",
    spec_prfi: "특별이익",
    spec_loss: "특별손실",
    thtr_ntin: "당기순이익",

    // 재무비율 / 성장성
    grs: "매출액증가율",
    bsop_prfi_inrt: "영업이익증가율",
    ntin_inrt: "순이익증가율",
    equt_inrt: "자기자본증가율",
    totl_aset_inrt: "총자산증가율",
    roe_val: "ROE",
    eps: "EPS",
    sps: "주당매출액",
    bps: "BPS",
    rsrv_rate: "유보비율",
    lblt_rate: "부채비율",

    // 수익성
    cptl_ntin_rate: "총자본순이익율",
    self_cptl_ntin_inrt: "자기자본순이익율",
    sale_ntin_rate: "매출액순이익율",
    sale_totl_rate: "매출액총이익율",

    // 안정성
    bram_depn: "차입금의존도",
    crnt_rate: "유동비율",
    quck_rate: "당좌비율",
};

/** 값이 비율(%)인 필드 — 표시 포맷을 나누기 위해 사용. */
export const RATIO_FIELDS = new Set([
    "grs", "bsop_prfi_inrt", "ntin_inrt", "equt_inrt", "totl_aset_inrt",
    "roe_val", "rsrv_rate", "lblt_rate",
    "cptl_ntin_rate", "self_cptl_ntin_inrt", "sale_ntin_rate", "sale_totl_rate",
    "bram_depn", "crnt_rate", "quck_rate",
]);

export const INFO_LABELS: Record<string, string> = {
    pdno: "상품번호",
    prdt_type_cd: "상품유형코드",
    prdt_name: "상품명",
    prdt_abrv_name: "상품약어명",
    prdt_eng_name: "상품영문명",
    prdt_eng_abrv_name: "상품영문약어명",
    std_pdno: "표준상품번호(ISIN)",
    shtn_pdno: "단축상품번호",
    scrt_grp_cls_code: "증권그룹구분코드",
    excg_dvsn_cd: "거래소구분코드",
    mket_id_cd: "시장ID코드",
    setl_mmdd: "결산월일",
    lstg_stqt: "상장주수",
    lstg_cptl_amt: "상장자본금액",
    cpta: "자본금",
    papr: "액면가",
    issu_pric: "발행가격",
    kospi200_item_yn: "KOSPI200 편입여부",
    scts_mket_lstg_dt: "유가증권시장 상장일",
    scts_mket_lstg_abol_dt: "유가증권시장 상장폐지일",
    kosdaq_mket_lstg_dt: "코스닥시장 상장일",
    kosdaq_mket_lstg_abol_dt: "코스닥시장 상장폐지일",
    frbd_mket_lstg_dt: "프리보드시장 상장일",
    std_idst_clsf_cd: "표준산업분류코드",
    std_idst_clsf_cd_name: "표준산업분류명",
    idx_bztp_lcls_cd_name: "지수업종 대분류",
    idx_bztp_mcls_cd_name: "지수업종 중분류",
    idx_bztp_scls_cd_name: "지수업종 소분류",
    ocr_no: "OCR번호",
    crfd_item_yn: "크라우드펀딩종목 여부",
    elec_scty_yn: "전자증권 여부",
    issu_istt_cd: "발행기관코드",
    etf_chas_erng_rt_dbnb: "ETF추적수익률배수",
    etf_cu_qty: "ETF CU수량",
    etf_txtn_type_cd: "ETF과세유형코드",
    etf_type_cd: "ETF유형코드",
    lstg_abol_dt: "상장폐지일자",
    nwst_odst_dvsn_cd: "신주구주구분코드",
    sbst_pric: "대용가격",
    thco_sbst_pric: "당사대용가격",
    tr_stop_yn: "거래정지여부",
    admn_item_yn: "관리종목여부",
    expd_dt: "만기일자",
};

export function labelOf(map: Record<string, string>, key: string): string {
    return map[key] ?? key;
}
