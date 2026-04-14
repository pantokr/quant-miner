from pydantic import BaseModel


class BalanceRequest(BaseModel):
    """주식잔고조회 요청 파라미터"""
    CANO: str
    ACNT_PRDT_CD: str = "01"
    AFHR_FLPR_YN: str = "N"
    OFL_YN: str = ""
    INQR_DVSN: str = "02"
    UNPR_DVSN: str = "01"
    FUND_STTL_ICLD_YN: str = "N"
    FNCG_AMT_AUTO_RDPT_YN: str = "N"
    PRCS_DVSN: str = "00"
    CTX_AREA_FK100: str = ""
    CTX_AREA_NK100: str = ""


class DailyCcldRequest(BaseModel):
    """주식일별주문체결조회 요청 파라미터"""
    CANO: str
    ACNT_PRDT_CD: str = "01"
    INQR_STRT_DT: str
    INQR_END_DT: str
    SLL_BUY_DVSN_CD: str = "00"    # 00:전체, 01:매도, 02:매수
    PDNO: str = ""
    CCLD_DVSN: str = "00"           # 00:전체, 01:체결, 02:미체결
    INQR_DVSN: str = "00"           # 00:역순, 01:정순
    INQR_DVSN_3: str = "00"
    INQR_DVSN_1: str = ""
    CTX_AREA_FK100: str = ""
    CTX_AREA_NK100: str = ""


class MinuteChartRequest(BaseModel):
    """주식당일분봉조회 요청 파라미터"""
    FID_COND_MRKT_DIV_CODE: str = "J"  # 시장분류코드 (J: 주식)
    FID_INPUT_ISCD: str                 # 종목코드 (ex. "005930")
    FID_INPUT_HOUR_1: str               # 조회 기준 시간 HHMMSS (해당 시간 이전 데이터 반환)
    FID_PW_DATA_INCU_YN: str = "Y"      # 과거 데이터 포함 여부
    FID_ETC_CLS_CODE: str = ""


class MinuteDailyChartRequest(BaseModel):
    """주식일별분봉조회 요청 파라미터 (FHKST03010230, 특정 날짜 지정)"""
    FID_COND_MRKT_DIV_CODE: str = "J"
    FID_INPUT_ISCD: str
    FID_INPUT_DATE_1: str             # 조회 날짜 YYYYMMDD
    FID_INPUT_HOUR_1: str             # 조회 기준 시각 HHMMSS (이전 데이터 반환)
    FID_PW_DATA_INCU_YN: str = "Y"   # 과거 데이터 포함 여부
    FID_FAKE_TICK_INCU_YN: str = "N"  # 허수틱 포함 여부


# ── 1순위 ────────────────────────────────────────────────

class PeriodOhlcvRequest(BaseModel):
    """국내주식기간별시세 요청 파라미터"""
    FID_COND_MRKT_DIV_CODE: str = "J"
    FID_INPUT_ISCD: str                     # 종목코드
    FID_INPUT_DATE_1: str                   # 시작일 YYYYMMDD
    FID_INPUT_DATE_2: str                   # 종료일 YYYYMMDD
    FID_PERIOD_DIV_CODE: str = "D"          # D:일 W:주 M:월 Y:년
    FID_ORG_ADJ_PRC: str = "0"             # 0:수정주가 1:원주가


class CurrentPriceRequest(BaseModel):
    """주식현재가 시세 요청 파라미터"""
    FID_COND_MRKT_DIV_CODE: str = "J"
    FID_INPUT_ISCD: str


# ── 2순위 ────────────────────────────────────────────────

class FluctuationRankRequest(BaseModel):
    """등락률 순위 요청 파라미터 (FHPST01710000)"""
    fid_cond_mrkt_div_code: str = "J"
    fid_cond_scr_div_code: str = "20170"
    fid_input_iscd: str = "0001"
    fid_rank_sort_cls_code: str = "0"       # 0:상승률 1:하락률 2:시가대비상승 3:시가대비하락
    fid_input_cnt_1: str = "0"
    fid_prc_cls_code: str = "1"
    fid_input_price_1: str = ""
    fid_input_price_2: str = ""
    fid_vol_cnt: str = ""
    fid_trgt_cls_code: str = "111111111"
    fid_trgt_exls_cls_code: str = "000000"
    fid_div_cls_code: str = "0"
    fid_rsfl_rate1: str = ""
    fid_rsfl_rate2: str = ""


class VolumeRankRequest(BaseModel):
    """거래량 순위 요청 파라미터 (FHPST01710000, scr_div_code=20171)"""
    fid_cond_mrkt_div_code: str = "J"
    fid_cond_scr_div_code: str = "20171"    # 거래량순위 화면코드
    fid_input_iscd: str = "0001"
    fid_rank_sort_cls_code: str = "0"       # 0:거래량 1:거래대금
    fid_input_cnt_1: str = "0"
    fid_prc_cls_code: str = "1"
    fid_input_price_1: str = ""
    fid_input_price_2: str = ""
    fid_vol_cnt: str = ""
    fid_trgt_cls_code: str = "111111111"
    fid_trgt_exls_cls_code: str = "000000"
    fid_div_cls_code: str = "0"


class ForeignInstRankRequest(BaseModel):
    """외국인/기관 순매수 순위 요청 파라미터 (FHPST01700000)"""
    fid_cond_mrkt_div_code: str = "J"
    fid_cond_scr_div_code: str = "20150"
    fid_input_iscd: str = "0001"
    fid_rank_sort_cls_code: str = "0"       # 0:순매수수량 1:순매수대금
    fid_trgt_cls_code: str = "1"            # 1:외국인 2:기관
    fid_trgt_exls_cls_code: str = "000000"
    fid_div_cls_code: str = "0"
    fid_input_cnt_1: str = ""
    fid_vol_cnt: str = ""
    fid_input_date_1: str = ""


class InvestorRequest(BaseModel):
    """주식현재가 투자자 요청 파라미터"""
    FID_COND_MRKT_DIV_CODE: str = "J"
    FID_INPUT_ISCD: str


# ── 3순위 ────────────────────────────────────────────────

class OrderBookRequest(BaseModel):
    """주식현재가 호가/예상체결 요청 파라미터"""
    FID_COND_MRKT_DIV_CODE: str = "J"
    FID_INPUT_ISCD: str


class ShortSellRequest(BaseModel):
    """공매도 현황 요청 파라미터"""
    FID_COND_MRKT_DIV_CODE: str = "J"
    FID_INPUT_ISCD: str
    FID_INPUT_DATE_1: str                   # 시작일 YYYYMMDD
    FID_INPUT_DATE_2: str                   # 종료일 YYYYMMDD


class CreditRequest(BaseModel):
    """신용잔고 요청 파라미터"""
    FID_COND_MRKT_DIV_CODE: str = "J"
    FID_INPUT_ISCD: str
    FID_INPUT_DATE_1: str
    FID_INPUT_DATE_2: str
