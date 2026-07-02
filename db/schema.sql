-- 자동 생성: shared/db_models.py 기반 (스키마 단일 소스)
-- 재생성: python -c "from db.schema import ..." 대신 db_models로부터 CreateTable 사용

CREATE TABLE IF NOT EXISTS kis_token (
	env VARCHAR(10) NOT NULL, 
	token TEXT NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (env)
);

CREATE TABLE IF NOT EXISTS stock_credit (
	id BIGSERIAL NOT NULL, 
	stock_code VARCHAR(10) NOT NULL, 
	trade_date DATE NOT NULL, 
	credit_qty BIGINT, 
	credit_amount BIGINT, 
	credit_rate NUMERIC(8, 2), 
	close_price BIGINT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (stock_code, trade_date)
);

CREATE TABLE IF NOT EXISTS stock_dividend (
	id BIGSERIAL NOT NULL, 
	stock_code VARCHAR(10) NOT NULL, 
	record_date DATE NOT NULL, 
	amount_per_share VARCHAR(20), 
	dividend_type VARCHAR(20), 
	pay_date DATE, 
	raw JSONB, 
	PRIMARY KEY (id), 
	UNIQUE (stock_code, record_date)
);

CREATE TABLE IF NOT EXISTS stock_estimate (
	id BIGSERIAL NOT NULL, 
	stock_code VARCHAR(10) NOT NULL, 
	period VARCHAR(6) NOT NULL, 
	data JSONB NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (stock_code, period)
);

CREATE TABLE IF NOT EXISTS stock_finance (
	id BIGSERIAL NOT NULL, 
	stock_code VARCHAR(10) NOT NULL, 
	finance_type VARCHAR(30) NOT NULL, 
	period_type CHAR(1) NOT NULL, 
	period VARCHAR(6) NOT NULL, 
	data JSONB NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (stock_code, finance_type, period_type, period)
);
CREATE INDEX IF NOT EXISTS idx_sf_code_type ON stock_finance (stock_code, finance_type, period_type);

CREATE TABLE IF NOT EXISTS stock_holiday (
	base_date DATE NOT NULL, 
	weekday_cd CHAR(2), 
	is_open BOOLEAN, 
	is_trade_day BOOLEAN, 
	is_settle BOOLEAN, 
	PRIMARY KEY (base_date)
);

CREATE TABLE IF NOT EXISTS stock_info (
	stock_code VARCHAR(10) NOT NULL, 
	name VARCHAR(100), 
	market VARCHAR(10), 
	sector VARCHAR(100), 
	listed_shares BIGINT, 
	listed_date DATE, 
	isin VARCHAR(20), 
	settlement_month VARCHAR(4), 
	raw JSONB, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (stock_code)
);

CREATE TABLE IF NOT EXISTS stock_investor_trend (
	id BIGSERIAL NOT NULL, 
	stock_code VARCHAR(10) NOT NULL, 
	trade_date DATE NOT NULL, 
	prsn_ntby_qty BIGINT, 
	frgn_ntby_qty BIGINT, 
	orgn_ntby_qty BIGINT, 
	prsn_ntby_amt BIGINT, 
	frgn_ntby_amt BIGINT, 
	orgn_ntby_amt BIGINT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (stock_code, trade_date)
);

CREATE TABLE IF NOT EXISTS stock_minute_chart (
	id BIGSERIAL NOT NULL, 
	stock_code VARCHAR(10) NOT NULL, 
	trade_date DATE NOT NULL, 
	trade_time VARCHAR(6) NOT NULL, 
	open_price BIGINT NOT NULL, 
	high_price BIGINT NOT NULL, 
	low_price BIGINT NOT NULL, 
	close_price BIGINT NOT NULL, 
	volume BIGINT NOT NULL, 
	cumul_amount BIGINT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (stock_code, trade_date, trade_time)
);
CREATE INDEX IF NOT EXISTS idx_smc_code_date ON stock_minute_chart (stock_code, trade_date);

CREATE TABLE IF NOT EXISTS stock_minute_no_data (
	stock_code VARCHAR(10) NOT NULL, 
	trade_date DATE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (stock_code, trade_date)
);

CREATE TABLE IF NOT EXISTS stock_ohlcv (
	id BIGSERIAL NOT NULL, 
	stock_code VARCHAR(10) NOT NULL, 
	period_type CHAR(1) NOT NULL, 
	base_date DATE NOT NULL, 
	open_price BIGINT NOT NULL, 
	high_price BIGINT NOT NULL, 
	low_price BIGINT NOT NULL, 
	close_price BIGINT NOT NULL, 
	volume BIGINT NOT NULL, 
	amount BIGINT NOT NULL, 
	change_sign CHAR(1), 
	change_val BIGINT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (stock_code, period_type, base_date)
);

CREATE TABLE IF NOT EXISTS stock_short_sell (
	id BIGSERIAL NOT NULL, 
	stock_code VARCHAR(10) NOT NULL, 
	trade_date DATE NOT NULL, 
	short_volume BIGINT, 
	short_amount BIGINT, 
	close_price BIGINT, 
	change_rate NUMERIC(8, 2), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (stock_code, trade_date)
);
