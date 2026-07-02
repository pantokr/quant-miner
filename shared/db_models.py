"""SQLAlchemy 모델 — DB 스키마 단일 소스.

현재 shared/db/*.py 의 CREATE_TABLE_SQL을 SQLAlchemy 모델로 옮긴 것.
스키마의 정본(single source of truth)이며, db/schema.sql 은 여기서 생성한다.

주의: 데이터 접근(upsert/query)은 당분간 기존 psycopg2 코드(shared/db/*.py)를 유지한다.
이 모델들은 스키마 정의·마이그레이션·문서화 용도로 사용한다.

DDL 생성 예:
    from sqlalchemy import create_engine
    from sqlalchemy.schema import CreateTable
    from shared.db_models import Base
    for t in Base.metadata.sorted_tables:
        print(str(CreateTable(t).compile(dialect=postgresql.dialect())) + ";")

또는 실제 DB에 생성:
    from shared.config import database_url
    engine = create_engine(database_url())
    Base.metadata.create_all(engine)
"""
from sqlalchemy import (
    BigInteger, Boolean, CHAR, Column, Date, DateTime, Index,
    Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class StockMinuteChart(Base):
    __tablename__ = "stock_minute_chart"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    trade_date = Column(Date, nullable=False)
    trade_time = Column(String(6), nullable=False)
    open_price = Column(BigInteger, nullable=False)
    high_price = Column(BigInteger, nullable=False)
    low_price = Column(BigInteger, nullable=False)
    close_price = Column(BigInteger, nullable=False)
    volume = Column(BigInteger, nullable=False)
    cumul_amount = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date", "trade_time"),
        Index("idx_smc_code_date", "stock_code", "trade_date"),
    )


class StockMinuteNoData(Base):
    """분봉 데이터 없는 날짜 표시 (휴장일, 조회 범위 초과 등)"""
    __tablename__ = "stock_minute_no_data"
    stock_code = Column(String(10), primary_key=True)
    trade_date = Column(Date, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StockOhlcv(Base):
    __tablename__ = "stock_ohlcv"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    period_type = Column(CHAR(1), nullable=False)  # D/W/M/Y
    base_date = Column(Date, nullable=False)
    open_price = Column(BigInteger, nullable=False)
    high_price = Column(BigInteger, nullable=False)
    low_price = Column(BigInteger, nullable=False)
    close_price = Column(BigInteger, nullable=False)
    volume = Column(BigInteger, nullable=False)
    amount = Column(BigInteger, nullable=False)
    change_sign = Column(CHAR(1))  # 1:상한 2:상승 3:보합 4:하한 5:하락
    change_val = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("stock_code", "period_type", "base_date"),)


class StockInvestorTrend(Base):
    __tablename__ = "stock_investor_trend"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    trade_date = Column(Date, nullable=False)
    prsn_ntby_qty = Column(BigInteger)  # 개인 순매수량
    frgn_ntby_qty = Column(BigInteger)  # 외국인 순매수량
    orgn_ntby_qty = Column(BigInteger)  # 기관 순매수량
    prsn_ntby_amt = Column(BigInteger)  # 개인 순매수대금
    frgn_ntby_amt = Column(BigInteger)  # 외국인 순매수대금
    orgn_ntby_amt = Column(BigInteger)  # 기관 순매수대금
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("stock_code", "trade_date"),)


class StockShortSell(Base):
    __tablename__ = "stock_short_sell"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    trade_date = Column(Date, nullable=False)
    short_volume = Column(BigInteger)
    short_amount = Column(BigInteger)
    close_price = Column(BigInteger)
    change_rate = Column(Numeric(8, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("stock_code", "trade_date"),)


class StockCredit(Base):
    __tablename__ = "stock_credit"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    trade_date = Column(Date, nullable=False)
    credit_qty = Column(BigInteger)
    credit_amount = Column(BigInteger)
    credit_rate = Column(Numeric(8, 2))
    close_price = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("stock_code", "trade_date"),)


class StockFinance(Base):
    __tablename__ = "stock_finance"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    finance_type = Column(String(30), nullable=False)  # balance_sheet / income_statement / ...
    period_type = Column(CHAR(1), nullable=False)  # A:연간 Q:분기
    period = Column(String(6), nullable=False)  # YYYYMM
    data = Column(JSONB, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("stock_code", "finance_type", "period_type", "period"),
        Index("idx_sf_code_type", "stock_code", "finance_type", "period_type"),
    )


class StockInfo(Base):
    __tablename__ = "stock_info"
    stock_code = Column(String(10), primary_key=True)
    name = Column(String(100))
    market = Column(String(10))
    sector = Column(String(100))
    listed_shares = Column(BigInteger)
    listed_date = Column(Date)
    isin = Column(String(20))
    settlement_month = Column(String(4))
    raw = Column(JSONB)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class StockDividend(Base):
    __tablename__ = "stock_dividend"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    record_date = Column(Date, nullable=False)
    amount_per_share = Column(String(20))
    dividend_type = Column(String(20))
    pay_date = Column(Date)
    raw = Column(JSONB)
    __table_args__ = (UniqueConstraint("stock_code", "record_date"),)


class StockEstimate(Base):
    __tablename__ = "stock_estimate"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False)
    period = Column(String(6), nullable=False)  # YYYYMM
    data = Column(JSONB, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("stock_code", "period"),)


class StockHoliday(Base):
    __tablename__ = "stock_holiday"
    base_date = Column(Date, primary_key=True)
    weekday_cd = Column(CHAR(2))       # 01:일 02:월 ... 07:토
    is_open = Column(Boolean)          # 개장 여부
    is_trade_day = Column(Boolean)     # 거래일 여부
    is_settle = Column(Boolean)        # 결제일 여부


class KisToken(Base):
    __tablename__ = "kis_token"
    env = Column(String(10), primary_key=True)  # 'real' or 'demo'
    token = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
