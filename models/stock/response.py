"""KIS OpenAPI 응답 모델 (오리지날 전체 필드).

필드 출처: KIS 공식 예제 리포지토리(open-trading-api/examples_llm)의
각 API `chk_*.py` 내 COLUMN_MAPPING 을 KIS MCP(로컬 8081)로 수집하여 재생성.

원칙:
- KIS 응답은 모두 문자열이므로 필드 타입은 str, 부분 응답 대비 기본값 "".
- output1(요약)과 output2(리스트)를 KIS 응답 스펙에 맞춰 분리.
- 라우터/서비스/DB가 소비하는 필드는 그대로 보존(별칭 포함).

예외(오리지날로 교체하지 않음):
- OrderBookResponse : askp1~10 raw 필드가 아닌, 서비스에서 배열로 가공한 전용 DTO.
- ShortSellResponse / CreditResponse : 프로젝트가 호출하는 엔드포인트
  (FHPST10010000 / FHKST01650300) 가 예제 리포의 API와 달라 매칭되는
  오리지날이 없음. DB 적재 필드(smtn_smvl / crdt_rmnd_*)에 맞춰 현행 유지.
- FinanceResponse / EstimateItem : 서비스가 raw dict 로 처리(모델 미사용).
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from .common import KisApiResponse


# ── 주식잔고조회 (inquire_balance / TTTC8434R) ──────────────

class StockBalanceItem(BaseModel):
    """잔고 output1 (보유종목)"""
    pdno: str = ""                  # 상품번호
    prdt_name: str = ""             # 상품명
    trad_dvsn_name: str = ""        # 매매구분명
    bfdy_buy_qty: str = ""          # 전일매수수량
    bfdy_sll_qty: str = ""          # 전일매도수량
    thdt_buyqty: str = ""           # 금일매수수량
    thdt_sll_qty: str = ""          # 금일매도수량
    hldg_qty: str = ""              # 보유수량
    ord_psbl_qty: str = ""          # 주문가능수량
    pchs_avg_pric: str = ""         # 매입평균가격
    pchs_amt: str = ""              # 매입금액
    prpr: str = ""                  # 현재가
    evlu_amt: str = ""              # 평가금액
    evlu_pfls_amt: str = ""         # 평가손익금액
    evlu_pfls_rt: str = ""          # 평가손익율
    evlu_erng_rt: str = ""          # 평가수익율
    loan_dt: str = ""               # 대출일자
    loan_amt: str = ""              # 대출금액
    stln_slng_chgs: str = ""        # 대주매각대금
    expd_dt: str = ""               # 만기일자
    fltt_rt: str = ""               # 등락율
    bfdy_cprs_icdc: str = ""        # 전일대비증감
    item_mgna_rt_name: str = ""     # 종목증거금율명
    grta_rt_name: str = ""          # 보증금율명
    sbst_pric: str = ""             # 대용가격
    stck_loan_unpr: str = ""        # 주식대출단가


class BalanceOutput2(BaseModel):
    """잔고 output2 (계좌 요약)"""
    dnca_tot_amt: str = ""          # 예수금총금액
    nxdy_excc_amt: str = ""         # 익일정산금액
    prvs_rcdl_excc_amt: str = ""    # 가수도정산금액
    cma_evlu_amt: str = ""          # CMA평가금액
    bfdy_buy_amt: str = ""          # 전일매수금액
    thdt_buy_amt: str = ""          # 금일매수금액
    nxdy_auto_rdpt_amt: str = ""    # 익일자동상환금액
    bfdy_sll_amt: str = ""          # 전일매도금액
    thdt_sll_amt: str = ""          # 금일매도금액
    d2_auto_rdpt_amt: str = ""      # D+2자동상환금액
    bfdy_tlex_amt: str = ""         # 전일제비용금액
    thdt_tlex_amt: str = ""         # 금일제비용금액
    tot_loan_amt: str = ""          # 총대출금액
    scts_evlu_amt: str = ""         # 유가평가금액
    tot_evlu_amt: str = ""          # 총평가금액
    nass_amt: str = ""              # 순자산금액
    fncg_gld_auto_rdpt_yn: str = "" # 융자금자동상환여부
    pchs_amt_smtl_amt: str = ""     # 매입금액합계금액
    evlu_amt_smtl_amt: str = ""     # 평가금액합계금액
    evlu_pfls_smtl_amt: str = ""    # 평가손익합계금액
    tot_stln_slng_chgs: str = ""    # 총대주매각대금
    bfdy_tot_asst_evlu_amt: str = "" # 전일총자산평가금액
    asst_icdc_amt: str = ""         # 자산증감액
    asst_icdc_erng_rt: str = ""     # 자산증감수익율


class BalanceResponse(KisApiResponse):
    output1: List[StockBalanceItem] = []
    output2: List[BalanceOutput2] = []


# ── 주식일별주문체결조회 (inquire_daily_ccld / TTTC0081R) ────

class DailyCcldItem(BaseModel):
    """일별체결 output1 (주문별 체결내역)"""
    ord_dt: str = ""                # 주문일자
    ord_gno_brno: str = ""          # 주문채번지점번호
    odno: str = ""                  # 주문번호
    orgn_odno: str = ""             # 원주문번호
    ord_dvsn_name: str = ""         # 주문구분명
    sll_buy_dvsn_cd: str = ""       # 매도매수구분코드
    sll_buy_dvsn_cd_name: str = ""  # 매도매수구분코드명
    pdno: str = ""                  # 상품번호
    prdt_name: str = ""             # 상품명
    ord_qty: str = ""               # 주문수량
    ord_unpr: str = ""              # 주문단가
    ord_tmd: str = ""               # 주문시각
    tot_ccld_qty: str = ""          # 총체결수량
    avg_prvs: str = ""              # 체결평균가 (체결금액 / 총체결수량)
    cncl_yn: str = ""               # 취소여부
    tot_ccld_amt: str = ""          # 총체결금액
    loan_dt: str = ""               # 대출일자
    ordr_empno: str = ""            # 주문자사번
    ord_dvsn_cd: str = ""           # 주문구분코드
    cnc_cfrm_qty: str = ""          # 취소확인수량
    rmn_qty: str = ""               # 잔여수량
    rjct_qty: str = ""              # 거부수량
    ccld_cndt_name: str = ""        # 체결조건명
    inqr_ip_addr: str = ""          # 조회IP주소
    cpbc_ordp_ord_rcit_dvsn_cd: str = ""   # 전산주문표주문접수구분코드
    cpbc_ordp_infm_mthd_dvsn_cd: str = ""  # 전산주문표통보방법구분코드
    infm_tmd: str = ""              # 통보시각
    ctac_tlno: str = ""             # 연락전화번호
    prdt_type_cd: str = ""          # 상품유형코드
    excg_dvsn_cd: str = ""          # 거래소구분코드
    cpbc_ordp_mtrl_dvsn_cd: str = "" # 전산주문표자료구분코드
    ord_orgno: str = ""             # 주문조직번호
    rsvn_ord_end_dt: str = ""       # 예약주문종료일자
    excg_id_dvsn_cd: str = ""       # 거래소ID구분코드
    stpm_cndt_pric: str = ""        # 스톱지정가조건가격
    stpm_efct_occr_dtmd: str = ""   # 스톱지정가효력발생상세시각


class DailyCcldSummary(BaseModel):
    """일별체결 output2 (합계)"""
    tot_ord_qty: str = ""           # 총주문수량
    tot_ccld_qty: str = ""          # 총체결수량
    pchs_avg_pric: str = ""         # 매입평균가격
    tot_ccld_amt: str = ""          # 총체결금액
    prsm_tlex_smtl: str = ""        # 추정제비용합계


class DailyCcldResponse(KisApiResponse):
    output1: List[DailyCcldItem] = []
    output2: List[DailyCcldSummary] = []


# ── 주식당일분봉조회 (inquire_time_itemchartprice) ──────────

class MinuteChartSummary(BaseModel):
    """당일분봉 output1 (현재가 요약)"""
    prdy_vrss: str = ""             # 전일 대비
    prdy_vrss_sign: str = ""        # 전일 대비 부호
    prdy_ctrt: str = ""             # 전일 대비율
    stck_prdy_clpr: str = ""        # 전일 종가
    acml_vol: str = ""              # 누적 거래량
    acml_tr_pbmn: str = ""          # 누적 거래대금
    hts_kor_isnm: str = ""          # 한글 종목명
    stck_prpr: str = ""             # 주식 현재가


class MinuteChartItem(BaseModel):
    """당일분봉 output2 (분봉)"""
    stck_bsop_date: str = ""        # 주식 영업일자
    stck_cntg_hour: str = ""        # 체결시간 (HHMMSS)
    stck_prpr: str = ""             # 현재가
    stck_oprc: str = ""             # 시가
    stck_hgpr: str = ""             # 최고가
    stck_lwpr: str = ""             # 최저가
    cntg_vol: str = ""              # 체결 거래량
    acml_vol: str = ""              # 누적거래량 (당일분봉만 제공)
    acml_tr_pbmn: str = ""          # 누적거래대금


class MinuteChartResponse(KisApiResponse):
    output1: Optional[MinuteChartSummary] = None
    output2: List[MinuteChartItem] = []


# ── 주식일별분봉조회 (inquire_time_dailychartprice / FHKST03010230) ─
# 당일과 달리 output2에 acml_vol(누적거래량) 없음

class MinuteDailyChartSummary(BaseModel):
    """일별분봉 output1 (요약)"""
    prdy_vrss: str = ""             # 전일 대비
    prdy_vrss_sign: str = ""        # 전일 대비 부호
    prdy_ctrt: str = ""             # 전일 대비율
    stck_prdy_clpr: str = ""        # 주식 전일 종가
    acml_vol: str = ""              # 누적 거래량
    acml_tr_pbmn: str = ""          # 누적 거래대금
    hts_kor_isnm: str = ""          # HTS 한글 종목명
    stck_prpr: str = ""             # 주식 현재가


class MinuteDailyChartItem(BaseModel):
    """일별분봉 output2 (분봉)"""
    stck_bsop_date: str = ""        # 영업일자 (YYYYMMDD)
    stck_cntg_hour: str = ""        # 체결시간 (HHMMSS)
    stck_prpr: str = ""             # 현재가 (종가)
    stck_oprc: str = ""             # 시가
    stck_hgpr: str = ""             # 최고가
    stck_lwpr: str = ""             # 최저가
    cntg_vol: str = ""              # 체결 거래량
    acml_tr_pbmn: str = ""          # 누적 거래대금


class MinuteDailyChartResponse(KisApiResponse):
    output1: Optional[MinuteDailyChartSummary] = None
    output2: List[MinuteDailyChartItem] = []


# ── 국내주식기간별시세 (inquire_daily_itemchartprice / FHKST03010100) ─

class OhlcvSummary(BaseModel):
    """기간별시세 output1 (종목 요약)"""
    stck_shrn_iscd: str = ""        # 주식 단축 종목코드
    hts_kor_isnm: str = ""          # HTS 한글 종목명
    stck_prpr: str = ""             # 주식 현재가
    prdy_vrss: str = ""             # 전일 대비
    prdy_vrss_sign: str = ""        # 전일 대비 부호
    prdy_ctrt: str = ""             # 전일 대비율
    prdy_vol: str = ""              # 전일 거래량
    prdy_vrss_vol: str = ""         # 전일 대비 거래량
    stck_mxpr: str = ""             # 주식 상한가
    stck_llam: str = ""             # 주식 하한가
    stck_prdy_oprc: str = ""        # 주식 전일 시가
    stck_prdy_hgpr: str = ""        # 주식 전일 최고가
    stck_prdy_lwpr: str = ""        # 주식 전일 최저가
    askp: str = ""                  # 매도호가
    bidp: str = ""                  # 매수호가
    vol_tnrt: str = ""              # 거래량 회전율
    stck_fcam: str = ""             # 주식 액면가
    lstn_stcn: str = ""             # 상장 주수
    cpfn: str = ""                  # 자본금
    hts_avls: str = ""              # HTS 시가총액
    per: str = ""                   # PER
    eps: str = ""                   # EPS
    pbr: str = ""                   # PBR
    itewhol_loan_rmnd_ratem: str = ""  # 전체 융자 잔고 비율


class OhlcvItem(BaseModel):
    """기간별시세 output2 (일/주/월/년 봉)"""
    stck_bsop_date: str = ""        # 영업일자
    stck_clpr: str = ""             # 종가
    stck_oprc: str = ""             # 시가
    stck_hgpr: str = ""             # 최고가
    stck_lwpr: str = ""             # 최저가
    acml_vol: str = ""              # 누적거래량
    acml_tr_pbmn: str = ""          # 누적거래대금
    flng_cls_code: str = ""         # 락 구분 코드
    prtt_rate: str = ""             # 분할 비율
    mod_yn: str = ""                # 변경 여부
    prdy_vrss_sign: str = ""        # 전일대비부호 (1:상한 2:상승 3:보합 4:하한 5:하락)
    prdy_vrss: str = ""             # 전일대비
    revl_issu_reas: str = ""        # 재평가사유코드


class OhlcvResponse(KisApiResponse):
    output1: Optional[OhlcvSummary] = None
    output2: List[OhlcvItem] = []


# ── 주식현재가 시세 (inquire_price / FHKST01010100) ─────────

class CurrentPriceItem(BaseModel):
    """현재가 output (단건)"""
    iscd_stat_cls_code: str = ""    # 종목 상태 구분 코드
    marg_rate: str = ""             # 증거금 비율
    rprs_mrkt_kor_name: str = ""    # 대표 시장 한글명
    new_hgpr_lwpr_cls_code: str = "" # 신 고가 저가 구분 코드
    bstp_kor_isnm: str = ""         # 업종 한글 종목명
    temp_stop_yn: str = ""          # 임시 정지 여부
    oprc_rang_cont_yn: str = ""     # 시가 범위 연장 여부
    clpr_rang_cont_yn: str = ""     # 종가 범위 연장 여부
    crdt_able_yn: str = ""          # 신용 가능 여부
    grmn_rate_cls_code: str = ""    # 보증금 비율 구분 코드
    elw_pblc_yn: str = ""           # ELW 발행 여부
    stck_prpr: str = ""             # 주식 현재가
    prdy_vrss: str = ""             # 전일 대비
    prdy_vrss_sign: str = ""        # 전일 대비 부호
    prdy_ctrt: str = ""             # 전일 대비율
    acml_tr_pbmn: str = ""          # 누적 거래 대금
    acml_vol: str = ""              # 누적 거래량
    prdy_vrss_vol_rate: str = ""    # 전일 대비 거래량 비율
    stck_oprc: str = ""             # 주식 시가
    stck_hgpr: str = ""             # 주식 최고가
    stck_lwpr: str = ""             # 주식 최저가
    stck_mxpr: str = ""             # 주식 상한가
    stck_llam: str = ""             # 주식 하한가
    stck_sdpr: str = ""             # 주식 기준가
    wghn_avrg_stck_prc: str = ""    # 가중 평균 주식 가격
    hts_frgn_ehrt: str = ""         # HTS 외국인 소진율
    frgn_ntby_qty: str = ""         # 외국인 순매수 수량
    pgtr_ntby_qty: str = ""         # 프로그램매매 순매수 수량
    pvt_scnd_dmrs_prc: str = ""     # 피벗 2차 저항 가격
    pvt_frst_dmrs_prc: str = ""     # 피벗 1차 저항 가격
    pvt_pont_val: str = ""          # 피벗 포인트 값
    pvt_frst_dmsp_prc: str = ""     # 피벗 1차 지지 가격
    pvt_scnd_dmsp_prc: str = ""     # 피벗 2차 지지 가격
    dmrs_val: str = ""              # 저항 값
    dmsp_val: str = ""              # 지지 값
    cpfn: str = ""                  # 자본금
    rstc_wdth_prc: str = ""         # 제한 폭 가격
    stck_fcam: str = ""             # 주식 액면가
    stck_sspr: str = ""             # 주식 대용가
    aspr_unit: str = ""             # 호가단위
    hts_deal_qty_unit_val: str = "" # HTS 매매 수량 단위 값
    lstn_stcn: str = ""             # 상장 주수
    hts_avls: str = ""              # HTS 시가총액
    per: str = ""                   # PER
    pbr: str = ""                   # PBR
    stac_month: str = ""            # 결산 월
    vol_tnrt: str = ""              # 거래량 회전율
    eps: str = ""                   # EPS
    bps: str = ""                   # BPS
    d250_hgpr: str = ""             # 250일 최고가
    d250_hgpr_date: str = ""        # 250일 최고가 일자
    d250_hgpr_vrss_prpr_rate: str = ""  # 250일 최고가 대비 현재가 비율
    d250_lwpr: str = ""             # 250일 최저가
    d250_lwpr_date: str = ""        # 250일 최저가 일자
    d250_lwpr_vrss_prpr_rate: str = ""  # 250일 최저가 대비 현재가 비율
    stck_dryy_hgpr: str = ""        # 주식 연중 최고가
    dryy_hgpr_vrss_prpr_rate: str = ""  # 연중 최고가 대비 현재가 비율
    dryy_hgpr_date: str = ""        # 연중 최고가 일자
    stck_dryy_lwpr: str = ""        # 주식 연중 최저가
    dryy_lwpr_vrss_prpr_rate: str = ""  # 연중 최저가 대비 현재가 비율
    dryy_lwpr_date: str = ""        # 연중 최저가 일자
    w52_hgpr: str = ""              # 52주일 최고가
    w52_hgpr_vrss_prpr_ctrt: str = ""   # 52주일 최고가 대비 현재가 대비
    w52_hgpr_date: str = ""         # 52주일 최고가 일자
    w52_lwpr: str = ""              # 52주일 최저가
    w52_lwpr_vrss_prpr_ctrt: str = ""   # 52주일 최저가 대비 현재가 대비
    w52_lwpr_date: str = ""         # 52주일 최저가 일자
    whol_loan_rmnd_rate: str = ""   # 전체 융자 잔고 비율
    ssts_yn: str = ""               # 공매도가능여부
    stck_shrn_iscd: str = ""        # 주식 단축 종목코드
    fcam_cnnm: str = ""             # 액면가 통화명
    cpfn_cnnm: str = ""             # 자본금 통화명
    apprch_rate: str = ""           # 접근도
    frgn_hldn_qty: str = ""         # 외국인 보유 수량
    vi_cls_code: str = ""           # VI적용구분코드
    ovtm_vi_cls_code: str = ""      # 시간외단일가VI적용구분코드
    last_ssts_cntg_qty: str = ""    # 최종 공매도 체결 수량
    invt_caful_yn: str = ""         # 투자유의여부
    mrkt_warn_cls_code: str = ""    # 시장경고코드
    short_over_yn: str = ""         # 단기과열여부
    sltr_yn: str = ""               # 정리매매여부
    mang_issu_cls_code: str = ""    # 관리종목여부


class CurrentPriceResponse(KisApiResponse):
    output: CurrentPriceItem = CurrentPriceItem()


# ── 등락률 순위 (fluctuation / FHPST01700000) ───────────────

class FluctuationRankItem(BaseModel):
    """등락률 순위 output"""
    stck_shrn_iscd: str = ""        # 주식 단축 종목코드
    data_rank: str = ""             # 데이터 순위
    hts_kor_isnm: str = ""          # HTS 한글 종목명
    stck_prpr: str = ""             # 주식 현재가
    prdy_vrss: str = ""             # 전일 대비
    prdy_vrss_sign: str = ""        # 전일 대비 부호
    prdy_ctrt: str = ""             # 전일 대비율
    acml_vol: str = ""              # 누적 거래량
    stck_hgpr: str = ""             # 주식 최고가
    hgpr_hour: str = ""             # 최고가 시간
    acml_hgpr_date: str = ""        # 누적 최고가 일자
    stck_lwpr: str = ""             # 주식 최저가
    lwpr_hour: str = ""             # 최저가 시간
    acml_lwpr_date: str = ""        # 누적 최저가 일자
    lwpr_vrss_prpr_rate: str = ""   # 저가 대비 현재가 비율
    dsgt_date_clpr_vrss_prpr_rate: str = ""  # 지정 일자 종가 대비 현재가 비율
    cnnt_ascn_dynu: str = ""        # 연속 상승 일수
    hgpr_vrss_prpr_rate: str = ""   # 고가 대비 현재가 비율
    cnnt_down_dynu: str = ""        # 연속 하락 일수
    oprc_vrss_prpr_sign: str = ""   # 시가 대비 부호
    oprc_vrss_prpr: str = ""        # 시가 대비
    oprc_vrss_prpr_rate: str = ""   # 시가 대비 현재가 비율
    prd_rsfl: str = ""              # 기간 등락
    prd_rsfl_rate: str = ""         # 기간 등락 비율
    # 호환: 오리지날 응답엔 없으나 라우터가 trade_value로 참조
    acml_tr_pbmn: str = ""          # 누적 거래대금


class FluctuationRankResponse(KisApiResponse):
    output: List[FluctuationRankItem] = []


# ── 거래량 순위 (volume_rank / FHPST01710000) ───────────────

class VolumeRankItem(BaseModel):
    """거래량 순위 output"""
    hts_kor_isnm: str = ""          # HTS 한글 종목명
    mksc_shrn_iscd: str = ""        # 유가증권 단축 종목코드
    data_rank: str = ""             # 데이터 순위
    stck_prpr: str = ""             # 주식 현재가
    prdy_vrss_sign: str = ""        # 전일 대비 부호
    prdy_vrss: str = ""             # 전일 대비
    prdy_ctrt: str = ""             # 전일 대비율
    acml_vol: str = ""              # 누적 거래량
    prdy_vol: str = ""              # 전일 거래량
    lstn_stcn: str = ""             # 상장 주식수
    avrg_vol: str = ""              # 평균 거래량
    n_befr_clpr_vrss_prpr_rate: str = ""  # N일전종가대비현재가(%)
    vol_inrt: str = ""              # 거래량 증가율
    vol_tnrt: str = ""              # 거래량 회전율
    nday_vol_tnrt: str = ""         # N일 거래량 회전율
    avrg_tr_pbmn: str = ""          # 평균 거래 대금
    tr_pbmn_tnrt: str = ""          # 거래대금 회전율
    nday_tr_pbmn_tnrt: str = ""     # N일 거래대금 회전율
    acml_tr_pbmn: str = ""          # 누적 거래 대금


class VolumeRankResponse(KisApiResponse):
    output: List[VolumeRankItem] = []


# ── 국내기관_외국인 매매종목가집계 (foreign_institution_total) ─

class ForeignInstRankItem(BaseModel):
    """외국인/기관 순매수 순위 output (가집계)"""
    hts_kor_isnm: str = ""          # HTS 한글 종목명
    mksc_shrn_iscd: str = ""        # 유가증권 단축 종목코드
    # 순매수 수량 (라이브 API는 ntby_cntg_qty 로 반환 → 별칭 허용)
    ntby_qty: str = Field(default="", alias="ntby_cntg_qty")
    stck_prpr: str = ""             # 주식 현재가
    prdy_vrss_sign: str = ""        # 전일 대비 부호
    prdy_vrss: str = ""             # 전일 대비
    prdy_ctrt: str = ""             # 전일 대비율
    acml_vol: str = ""              # 누적 거래량
    frgn_ntby_qty: str = ""         # 외국인 순매수 수량
    orgn_ntby_qty: str = ""         # 기관계 순매수 수량
    ivtr_ntby_qty: str = ""         # 투자신탁 순매수 수량
    bank_ntby_qty: str = ""         # 은행 순매수 수량
    insu_ntby_qty: str = ""         # 보험 순매수 수량
    mrbn_ntby_qty: str = ""         # 종금 순매수 수량
    fund_ntby_qty: str = ""         # 기금 순매수 수량
    etc_orgt_ntby_vol: str = ""     # 기타 단체 순매수 거래량
    etc_corp_ntby_vol: str = ""     # 기타 법인 순매수 거래량
    frgn_ntby_tr_pbmn: str = ""     # 외국인 순매수 거래 대금
    orgn_ntby_tr_pbmn: str = ""     # 기관계 순매수 거래 대금
    ivtr_ntby_tr_pbmn: str = ""     # 투자신탁 순매수 거래 대금
    bank_ntby_tr_pbmn: str = ""     # 은행 순매수 거래 대금
    insu_ntby_tr_pbmn: str = ""     # 보험 순매수 거래 대금
    mrbn_ntby_tr_pbmn: str = ""     # 종금 순매수 거래 대금
    fund_ntby_tr_pbmn: str = ""     # 기금 순매수 거래 대금
    etc_orgt_ntby_tr_pbmn: str = "" # 기타 단체 순매수 거래 대금
    etc_corp_ntby_tr_pbmn: str = "" # 기타 법인 순매수 거래 대금
    # 순위(라우터는 enumerate 사용) / 순매수대금 (라이브 API ntby_tr_pbmn) — 호환 필드
    data_rank: str = "0"
    ntby_pbmn: str = Field(default="0", alias="ntby_tr_pbmn")

    model_config = {"populate_by_name": True}


class ForeignInstRankResponse(KisApiResponse):
    output: List[ForeignInstRankItem] = []


# ── 주식현재가 투자자 (inquire_investor / FHKST01010900) ─────

class InvestorItem(BaseModel):
    """투자자 매매동향 output2"""
    stck_bsop_date: str = ""        # 영업일자
    stck_clpr: str = ""             # 종가
    prdy_vrss: str = ""             # 전일 대비
    prdy_vrss_sign: str = ""        # 전일 대비 부호
    prsn_ntby_qty: str = ""         # 개인 순매수 수량
    frgn_ntby_qty: str = ""         # 외국인 순매수 수량
    orgn_ntby_qty: str = ""         # 기관계 순매수 수량
    prsn_ntby_tr_pbmn: str = ""     # 개인 순매수 거래 대금
    frgn_ntby_tr_pbmn: str = ""     # 외국인 순매수 거래 대금
    orgn_ntby_tr_pbmn: str = ""     # 기관계 순매수 거래 대금
    prsn_shnu_vol: str = ""         # 개인 매수 거래량
    frgn_shnu_vol: str = ""         # 외국인 매수 거래량
    orgn_shnu_vol: str = ""         # 기관계 매수 거래량
    prsn_shnu_tr_pbmn: str = ""     # 개인 매수 거래 대금
    frgn_shnu_tr_pbmn: str = ""     # 외국인 매수 거래 대금
    orgn_shnu_tr_pbmn: str = ""     # 기관계 매수 거래 대금
    prsn_seln_vol: str = ""         # 개인 매도 거래량
    frgn_seln_vol: str = ""         # 외국인 매도 거래량
    orgn_seln_vol: str = ""         # 기관계 매도 거래량
    prsn_seln_tr_pbmn: str = ""     # 개인 매도 거래 대금
    frgn_seln_tr_pbmn: str = ""     # 외국인 매도 거래 대금
    orgn_seln_tr_pbmn: str = ""     # 기관계 매도 거래 대금


class InvestorResponse(KisApiResponse):
    output1: dict = {}
    output2: List[InvestorItem] = []


# ── 호가/예상체결 (가공 DTO, 오리지날 미러 아님) ──────────────
# 서비스(services/quote/orderbook.py)가 raw askp1~10 을 배열로 가공하여 생성.

class AskBidLevel(BaseModel):
    price: int
    quantity: int


class OrderBookResponse(KisApiResponse):
    """호가/예상체결 (전용 가공 DTO)"""
    ask_prices: List[int] = []    # 매도호가 (낮은가격 → 높은가격)
    bid_prices: List[int] = []    # 매수호가 (높은가격 → 낮은가격)
    ask_quantities: List[int] = []
    bid_quantities: List[int] = []
    total_ask_qty: int = 0
    total_bid_qty: int = 0
    expected_price: str = ""      # 예상체결가


# ── 공매도 (FHPST10010000, 프로젝트 전용 — 오리지날 미매칭) ───
# examples_llm 의 daily_short_sale(FHPST04830000)와 다른 API이므로 현행 유지.
# DB(db/stock_short.py)가 smtn_smvl / smtn_tr_pbmn 을 적재.

class ShortSellItem(BaseModel):
    """공매도 아이템"""
    stck_bsop_date: str = ""   # 영업일자
    smtn_smvl: str = ""        # 공매도거래량
    smtn_tr_pbmn: str = ""     # 공매도거래대금
    stck_prpr: str = ""        # 현재가
    prdy_ctrt: str = ""        # 전일대비율


class ShortSellResponse(KisApiResponse):
    output1: List[ShortSellItem] = []


# ── 신용잔고 (FHKST01650300, 프로젝트 전용 — 오리지날 미매칭) ─
# DB(db/stock_short.py)가 crdt_rmnd_qty / crdt_rmnd_amt / crdt_rmnd_rate 를 적재.

class CreditItem(BaseModel):
    """신용잔고 아이템"""
    stck_bsop_date: str = ""    # 영업일자
    crdt_rmnd_qty: str = ""     # 신용잔고수량
    crdt_rmnd_amt: str = ""     # 신용잔고금액
    crdt_rmnd_rate: str = ""    # 신용잔고율
    stck_prpr: str = ""         # 현재가


class CreditResponse(KisApiResponse):
    output1: List[CreditItem] = []


# ── 재무/기업정보 ──────────────────────────────────────────
# 서비스(services/finance/*)는 raw dict 로 처리 → 모델은 참조/문서용.

class FinanceItem(BaseModel):
    """재무정보 아이템 (재무상태표/손익계산서/재무비율 등 공통)
    KIS API가 기간별로 다양한 필드를 반환하므로 raw dict로 저장
    """
    model_config = {"extra": "allow"}

    stac_yymm: str = ""     # 결산년월 (YYYYMM)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class FinanceResponse(KisApiResponse):
    output: List[Dict[str, Any]] = []


class StockInfoItem(BaseModel):
    """주식기본조회 output (search_stock_info)"""
    model_config = {"extra": "allow"}

    pdno: str = ""                  # 상품번호
    prdt_type_cd: str = ""          # 상품유형코드
    prdt_name: str = ""             # 상품명
    prdt_name120: str = ""          # 상품명(120자)
    prdt_abrv_name: str = ""        # 상품약어명
    prdt_eng_name: str = ""         # 상품영문명
    prdt_eng_name120: str = ""      # 상품영문명(120자)
    prdt_eng_abrv_name: str = ""    # 상품영문약어명
    mket_id_cd: str = ""            # 시장ID코드
    scty_grp_id_cd: str = ""        # 증권그룹ID코드
    excg_dvsn_cd: str = ""          # 거래소구분코드
    setl_mmdd: str = ""             # 결산월일
    lstg_stqt: str = ""             # 상장주수
    lstg_cptl_amt: str = ""         # 상장자본금액
    cpta: str = ""                  # 자본금
    papr: str = ""                  # 액면가
    issu_pric: str = ""             # 발행가격
    kospi200_item_yn: str = ""      # 코스피200종목여부
    scts_mket_lstg_dt: str = ""     # 유가증권시장상장일자
    scts_mket_lstg_abol_dt: str = "" # 유가증권시장상장폐지일자
    kosdaq_mket_lstg_dt: str = ""   # 코스닥시장상장일자
    kosdaq_mket_lstg_abol_dt: str = "" # 코스닥시장상장폐지일자
    frbd_mket_lstg_dt: str = ""     # 프리보드시장상장일자
    frbd_mket_lstg_abol_dt: str = "" # 프리보드시장상장폐지일자
    reits_kind_cd: str = ""         # 리츠종류코드
    etf_dvsn_cd: str = ""           # ETF구분코드
    oilf_fund_yn: str = ""          # 유전펀드여부
    idx_bztp_lcls_cd: str = ""      # 지수업종대분류코드
    idx_bztp_mcls_cd: str = ""      # 지수업종중분류코드
    idx_bztp_scls_cd: str = ""      # 지수업종소분류코드
    idx_bztp_lcls_cd_name: str = "" # 지수업종대분류코드명
    idx_bztp_mcls_cd_name: str = "" # 지수업종중분류코드명
    idx_bztp_scls_cd_name: str = "" # 지수업종소분류코드명
    stck_kind_cd: str = ""          # 주식종류코드
    mfnd_opng_dt: str = ""          # 뮤추얼펀드개시일자
    mfnd_end_dt: str = ""           # 뮤추얼펀드종료일자
    dpsi_erlm_cncl_dt: str = ""     # 예탁등록취소일자
    etf_cu_qty: str = ""            # ETFCU수량
    std_pdno: str = ""              # 표준상품번호 (ISIN)
    dpsi_aptm_erlm_yn: str = ""     # 예탁지정등록여부
    etf_txtn_type_cd: str = ""      # ETF과세유형코드
    etf_type_cd: str = ""           # ETF유형코드
    lstg_abol_dt: str = ""          # 상장폐지일자
    nwst_odst_dvsn_cd: str = ""     # 신주구주구분코드
    sbst_pric: str = ""             # 대용가격
    thco_sbst_pric: str = ""        # 당사대용가격
    thco_sbst_pric_chng_dt: str = "" # 당사대용가격변경일자
    tr_stop_yn: str = ""            # 거래정지여부
    admn_item_yn: str = ""          # 관리종목여부
    thdt_clpr: str = ""             # 당일종가
    bfdy_clpr: str = ""             # 전일종가
    clpr_chng_dt: str = ""          # 종가변경일자
    std_idst_clsf_cd: str = ""      # 표준산업분류코드
    std_idst_clsf_cd_name: str = "" # 표준산업분류코드명
    ocr_no: str = ""                # OCR번호
    crfd_item_yn: str = ""          # 크라우드펀딩종목여부
    elec_scty_yn: str = ""          # 전자증권여부
    issu_istt_cd: str = ""          # 발행기관코드
    etf_chas_erng_rt_dbnb: str = "" # ETF추적수익율배수
    etf_etn_ivst_heed_item_yn: str = "" # ETFETN투자유의종목여부
    stln_int_rt_dvsn_cd: str = ""   # 대주이자율구분코드
    frnr_psnl_lmt_rt: str = ""      # 외국인개인한도비율
    lstg_rqsr_issu_istt_cd: str = "" # 상장신청인발행기관코드
    lstg_rqsr_item_cd: str = ""     # 상장신청인종목코드
    trst_istt_issu_istt_cd: str = "" # 신탁기관발행기관코드
    cptt_trad_tr_psbl_yn: str = ""  # NXT 거래종목여부
    nxt_tr_stop_yn: str = ""        # NXT 거래정지여부


class StockInfoResponse(KisApiResponse):
    output: Optional[Dict[str, Any]] = None


class HolidayItem(BaseModel):
    """영업일조회 output"""
    bass_dt: str = ""       # 기준일자
    wday_dvsn_cd: str = ""  # 요일구분코드 (01:일 02:월 ... 07:토)
    bzdy_yn: str = ""       # 영업일여부 (Y/N)
    tr_day_yn: str = ""     # 거래일여부
    opnd_yn: str = ""       # 개장일여부
    sttl_day_yn: str = ""   # 결제일여부


class HolidayResponse(KisApiResponse):
    output: List[HolidayItem] = []
    CTX_AREA_FK: str = ""
    CTX_AREA_NK: str = ""


class DividendItem(BaseModel):
    """예탁원정보 배당일정 output"""
    model_config = {"extra": "allow"}

    record_date: str = ""       # 기준일
    sht_cd: str = ""            # 종목코드
    divi_kind: str = ""         # 배당종류
    face_val: str = ""          # 액면가
    per_sto_divi_amt: str = ""  # 현금배당금 (1주당)
    divi_rate: str = ""         # 현금배당률(%)
    stk_divi_rate: str = ""     # 주식배당률(%)
    divi_pay_dt: str = ""       # 배당금지급일
    stk_div_pay_dt: str = ""    # 주식배당지급일
    odd_pay_dt: str = ""        # 단주대금지급일
    stk_kind: str = ""          # 주식종류
    high_divi_gb: str = ""      # 고배당종목여부


class DividendResponse(KisApiResponse):
    output: List[DividendItem] = []


class EstimateItem(BaseModel):
    """추정실적 아이템
    ※ estimate_perform(HHKST668300C0)은 output1~4 구조가 복잡하고 예제
      COLUMN_MAPPING이 부정확하여, 서비스에서 사용하는 실측 필드 기준 유지.
    """
    model_config = {"extra": "allow"}

    stac_yymm: str = ""     # 결산년월
    sale_account: str = ""  # 매출액
    sale_totl_prfi: str = "" # 매출총이익
    bsop_prti: str = ""     # 영업이익
    op_prfi: str = ""       # 세전순이익
    thtr_ntin: str = ""     # 당기순이익
    eps: str = ""           # EPS


class EstimateResponse(KisApiResponse):
    output: List[EstimateItem] = []
