from pydantic import BaseModel, Field
from typing import List, Optional
from .common import KisApiResponse


# --- 주식잔고조회 ---

class StockBalanceItem(BaseModel):
    pdno: str           # 상품번호
    prdt_name: str      # 상품명
    hldg_qty: str       # 보유수량
    pchs_avg_pric: str  # 매입평균단가
    prpr: str           # 현재가
    evlu_amt: str       # 평가금액
    evlu_pfls_amt: str  # 평가손익금액
    evlu_pfls_rt: str   # 평가손익률


class BalanceOutput2(BaseModel):
    dnca_tot_amt: str       # 예수금총액
    nxdy_excc_amt: str      # 익일정산금액
    pchs_amt_smtl_amt: str  # 매입금액합계금액
    evlu_amt_smtl_amt: str  # 평가금액합계금액
    evlu_pfls_smtl_amt: str  # 평가손익합계금액
    tot_evlu_amt: str       # 총평가금액


class BalanceResponse(KisApiResponse):
    output1: List[StockBalanceItem] = []
    output2: List[BalanceOutput2] = []


# --- 주식일별주문체결조회 ---

class DailyCcldItem(BaseModel):
    ord_dt: str                 # 주문일자
    ord_gno_brno: str           # 주문채번지점번호
    odno: str                   # 주문번호
    orgn_odno: str              # 원주문번호
    ord_dvsn_name: str          # 주문구분명
    sll_buy_dvsn_cd: str        # 매도매수구분코드
    sll_buy_dvsn_cd_name: str   # 매도매수구분코드명
    pdno: str                   # 상품번호
    prdt_name: str              # 상품명
    ord_qty: str                # 주문수량
    ord_unpr: str               # 주문단가
    tot_ccld_qty: str           # 총체결수량
    avg_prc: str                # 체결평균가
    tot_ccld_amt: str           # 총체결금액


class DailyCcldResponse(KisApiResponse):
    output1: List[DailyCcldItem] = []


# --- 주식당일분봉조회 ---

class MinuteChartItem(BaseModel):
    stck_cntg_hour: str  # 체결시간 (HHMMSS)
    stck_prpr: str      # 현재가
    stck_oprc: str      # 시가
    stck_hgpr: str      # 최고가
    stck_lwpr: str      # 최저가
    cntg_vol: str       # 체결량
    acml_vol: str       # 누적거래량
    acml_tr_pbmn: str   # 누적거래대금


class MinuteChartResponse(KisApiResponse):
    output1: dict = {}                  # 현재가 요약 (단건)
    output2: List[MinuteChartItem] = []  # 분봉 리스트


# --- 주식일별분봉조회 (과거 날짜) ---
# 당일과 달리 acml_vol(누적거래량) 없음, stck_bsop_date(영업일자) 추가

class MinuteDailyChartItem(BaseModel):
    stck_bsop_date: str  # 영업일자 (YYYYMMDD)
    stck_cntg_hour: str  # 체결시간 (HHMMSS)
    stck_prpr: str      # 현재가 (종가)
    stck_oprc: str      # 시가
    stck_hgpr: str      # 최고가
    stck_lwpr: str      # 최저가
    cntg_vol: str       # 체결량
    acml_tr_pbmn: str   # 누적거래대금


class MinuteDailyChartResponse(KisApiResponse):
    output1: dict = {}
    output2: List[MinuteDailyChartItem] = []


# ── 1순위 ────────────────────────────────────────────────

class OhlcvItem(BaseModel):
    """기간별시세 아이템"""
    stck_bsop_date: str  # 영업일자
    stck_oprc: str       # 시가
    stck_hgpr: str       # 최고가
    stck_lwpr: str       # 최저가
    stck_clpr: str       # 종가
    acml_vol: str        # 누적거래량
    acml_tr_pbmn: str    # 누적거래대금
    prdy_vrss: str       # 전일대비
    prdy_vrss_sign: str  # 전일대비부호 (1:상한 2:상승 3:보합 4:하한 5:하락)


class OhlcvResponse(KisApiResponse):
    output1: dict = {}
    output2: List[OhlcvItem] = []


class CurrentPriceItem(BaseModel):
    """주식현재가 시세"""
    stck_prpr: str      # 현재가
    stck_oprc: str      # 시가
    stck_hgpr: str      # 최고가
    stck_lwpr: str      # 최저가
    prdy_vrss: str      # 전일대비
    prdy_vrss_sign: str  # 전일대비부호
    prdy_ctrt: str      # 전일대비율
    acml_vol: str       # 누적거래량
    acml_tr_pbmn: str   # 누적거래대금
    hts_avls: str       # 시가총액
    per: str            # PER
    pbr: str            # PBR
    eps: str            # EPS
    bps: str            # BPS
    hts_frgn_ehrt: str  # 외국인보유율
    frgn_ntby_qty: str  # 외국인순매수수량


class CurrentPriceResponse(KisApiResponse):
    output: CurrentPriceItem


# ── 2순위 ────────────────────────────────────────────────

class RankItem(BaseModel):
    """등락률 순위 아이템"""
    hts_kor_isnm: str   # 종목명
    mksc_shrn_iscd: str  # 종목코드
    data_rank: str      # 순위
    stck_prpr: str      # 현재가
    prdy_vrss: str      # 전일대비
    prdy_vrss_sign: str  # 전일대비부호
    prdy_ctrt: str      # 등락률
    acml_vol: str       # 거래량
    acml_tr_pbmn: str = ""  # 거래대금


class RankResponse(KisApiResponse):
    output: List[RankItem] = []


class VolumeRankItem(BaseModel):
    """거래량 순위 아이템"""
    hts_kor_isnm: str   # 종목명
    mksc_shrn_iscd: str  # 종목코드
    data_rank: str      # 순위
    stck_prpr: str      # 현재가
    prdy_ctrt: str      # 등락률
    acml_vol: str       # 거래량
    acml_tr_pbmn: str   # 거래대금


class VolumeRankResponse(KisApiResponse):
    output: List[VolumeRankItem] = []


class ForeignInstRankItem(BaseModel):
    """외국인/기관 순매수 순위 아이템 (가집계)"""
    hts_kor_isnm: str   # 종목명
    mksc_shrn_iscd: str  # 종목코드
    data_rank: str = "0"
    stck_prpr: str      # 현재가
    prdy_ctrt: str      # 등락률
    ntby_qty: str = Field(alias="ntby_cntg_qty")  # 순매수수량
    # 순매수대금 (일부 API에서 누락될 수 있음)
    ntby_pbmn: str = Field(alias="ntby_tr_pbmn", default="0")

    class Config:
        populate_by_name = True


class ForeignInstRankResponse(KisApiResponse):
    output: List[ForeignInstRankItem] = []


class InvestorItem(BaseModel):
    """투자자 매매동향 아이템"""
    stck_bsop_date: str  # 영업일자
    prsn_ntby_qty: str   # 개인 순매수량
    frgn_ntby_qty: str   # 외국인 순매수량
    orgn_ntby_qty: str   # 기관 순매수량
    prsn_ntby_tr_pbmn: str  # 개인 순매수대금
    frgn_ntby_tr_pbmn: str  # 외국인 순매수대금
    orgn_ntby_tr_pbmn: str  # 기관 순매수대금


class InvestorResponse(KisApiResponse):
    output1: dict = {}
    output2: List[InvestorItem] = []


# ── 3순위 ────────────────────────────────────────────────

class AskBidLevel(BaseModel):
    price: int
    quantity: int


class OrderBookResponse(KisApiResponse):
    """호가/예상체결"""
    ask_prices: List[int] = []    # 매도호가 (낮은가격 → 높은가격)
    bid_prices: List[int] = []    # 매수호가 (높은가격 → 낮은가격)
    ask_quantities: List[int] = []
    bid_quantities: List[int] = []
    total_ask_qty: int = 0
    total_bid_qty: int = 0
    expected_price: str = ""      # 예상체결가


class ShortSellItem(BaseModel):
    """공매도 아이템"""
    stck_bsop_date: str   # 영업일자
    smtn_smvl: str        # 공매도거래량
    smtn_tr_pbmn: str     # 공매도거래대금
    stck_prpr: str        # 현재가
    prdy_ctrt: str        # 전일대비율


class ShortSellResponse(KisApiResponse):
    output1: List[ShortSellItem] = []


class CreditItem(BaseModel):
    """신용잔고 아이템"""
    stck_bsop_date: str    # 영업일자
    crdt_rmnd_qty: str     # 신용잔고수량
    crdt_rmnd_amt: str     # 신용잔고금액
    crdt_rmnd_rate: str    # 신용잔고율
    stck_prpr: str         # 현재가


class CreditResponse(KisApiResponse):
    output1: List[CreditItem] = []
