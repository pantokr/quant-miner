from pydantic import BaseModel


class BalanceRequest(BaseModel):
    """주식잔고조회 요청 파라미터"""
    CANO: str
    ACNT_PRDT_CD: str = "01"
    AFHR_FLPR_YN: str = "N"        # 시간외단일가여부 N:기본값 Y:시간외단일가
    OFL_YN: str = ""               # 오프라인여부 (공란)
    INQR_DVSN: str = "00"          # 조회구분 00:전체
    UNPR_DVSN: str = "01"          # 단가구분 01:기본값
    FUND_STTL_ICLD_YN: str = "N"   # 펀드결제포함여부 N:미포함 Y:포함
    FNCG_AMT_AUTO_RDPT_YN: str = "N"  # 융자금액자동상환여부 N:기본값
    PRCS_DVSN: str = "00"          # 00:전일매매포함 01:전일매매미포함
    COST_ICLD_YN: str = ""         # 비용포함여부
    CTX_AREA_FK100: str = ""       # 연속조회검색조건100 (최초조회: 공란)
    CTX_AREA_NK100: str = ""       # 연속조회키100 (최초조회: 공란)


class DailyCcldRequest(BaseModel):
    """주식일별주문체결조회 요청 파라미터"""
    CANO: str
    ACNT_PRDT_CD: str = "01"
    INQR_STRT_DT: str                      # 조회시작일자 YYYYMMDD
    INQR_END_DT: str                        # 조회종료일자 YYYYMMDD
    SLL_BUY_DVSN_CD: str = "00"            # 00:전체 01:매도 02:매수
    PDNO: str = ""                          # 종목번호 (6자리, 선택)
    ORD_GNO_BRNO: str = ""                  # 주문채번지점번호
    ODNO: str = ""                          # 주문번호 (선택)
    CCLD_DVSN: str = "00"                  # 00:전체 01:체결 02:미체결
    INQR_DVSN: str = "00"                  # 00:역순 01:정순
    INQR_DVSN_1: str = ""                  # 없음:전체 1:ELW 2:프리보드
    INQR_DVSN_3: str = "00"               # 00:전체 01:현금 02:신용 03:담보 ...
    EXCG_ID_DVSN_CD: str = "KRX"          # KRX / NXT / SOR / ALL (모의: KRX만)
    CTX_AREA_FK100: str = ""               # 연속조회검색조건100 (최초조회: 공란)
    CTX_AREA_NK100: str = ""               # 연속조회키100 (최초조회: 공란)


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
    FID_RSFL_RATE2: str = ""
    FID_COND_MRKT_DIV_CODE: str = "J"
    FID_COND_SCR_DIV_CODE: str = "20170"
    FID_INPUT_ISCD: str = "0001"
    FID_RANK_SORT_CLS_CODE: str = "0"       # 0:상승률 1:하락률 2:시가대비상승 3:시가대비하락
    FID_INPUT_CNT_1: str = "0"
    FID_PRC_CLS_CODE: str = "1"
    FID_INPUT_PRICE_1: str = ""
    FID_INPUT_PRICE_2: str = ""
    FID_VOL_CNT: str = ""
    FID_TRGT_CLS_CODE: str = "0"
    FID_TRGT_EXLS_CLS_CODE: str = "0"
    FID_DIV_CLS_CODE: str = "0"
    FID_RSFL_RATE1: str = ""


class VolumeRankRequest(BaseModel):
    """거래량 순위 요청 파라미터 (FHPST01710000, scr_div_code=20171)"""
    FID_COND_MRKT_DIV_CODE: str = "J"
    FID_COND_SCR_DIV_CODE: str = "20171"    # 거래량순위 화면코드
    FID_INPUT_ISCD: str = "0000"
    FID_DIV_CLS_CODE: str = "0"
    FID_BLNG_CLS_CODE: str = "0"
    FID_TRGT_CLS_CODE: str = "111111111"
    FID_TRGT_EXLS_CLS_CODE: str = "0000000000"
    FID_INPUT_PRICE_1: str = ""
    FID_INPUT_PRICE_2: str = ""
    FID_VOL_CNT: str = ""
    FID_INPUT_DATE_1: str = "0"


class ForeignInstRankRequest(BaseModel):
    """외국인/기관 순매수 순위 요청 파라미터 (FHPST01700000)"""
    FID_COND_MRKT_DIV_CODE: str = "J"
    FID_COND_SCR_DIV_CODE: str = "20150"
    FID_INPUT_ISCD: str = "0001"
    FID_RANK_SORT_CLS_CODE: str = "0"       # 0:순매수수량 1:순매수대금
    FID_TRGT_CLS_CODE: str = "1"            # 1:외국인 2:기관
    FID_TRGT_EXLS_CLS_CODE: str = "000000"
    FID_DIV_CLS_CODE: str = "0"
    FID_INPUT_CNT_1: str = ""
    FID_VOL_CNT: str = ""
    FID_INPUT_DATE_1: str = ""


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


# ── 재무/기업정보 ──────────────────────────────────────────

class FinanceRequest(BaseModel):
    """재무정보 공통 요청 파라미터 (재무상태표/손익계산서/재무비율 등)"""
    FID_DIV_CLS_CODE: str = "0"            # 0:연 1:분기
    FID_COND_MRKT_DIV_CODE: str = "J"      # 시장구분
    FID_INPUT_ISCD: str                    # 종목코드


class SearchStockInfoRequest(BaseModel):
    """주식기본조회 요청 파라미터 (CTPF1002R)"""
    PRDT_TYPE_CD: str = "300"              # 300:주식/ETF/ETN/ELW  302:채권  306:ELS
    PDNO: str                              # 종목번호 (6자리)


class HolidayRequest(BaseModel):
    """영업일조회 요청 파라미터 (CTCA0903R)"""
    BASS_DT: str                           # 기준일자 YYYYMMDD
    CTX_AREA_FK: str = ""                  # 연속조회검색조건
    CTX_AREA_NK: str = ""                  # 연속조회키


class DividendRequest(BaseModel):
    """배당금 조회 요청 파라미터 (HHKDB669102C0)"""
    SHT_CD: str                            # 종목코드
    F_DT: str                              # 시작일 YYYYMMDD
    T_DT: str                              # 종료일 YYYYMMDD
    GB1: str = ""
    CTS: str = ""
    HIGH_GB: str = ""


class EstimatePerformRequest(BaseModel):
    """추정실적 요청 파라미터 (HHKST668300C0)"""
    SHT_CD: str                            # 종목코드
