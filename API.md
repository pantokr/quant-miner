
# Quant Miner API 엔드포인트

베이스 URL: `http://168.107.24.190:8000`  
로컬 URL: `http://127.0.0.1:8000`  
Swagger UI: `{BASE_URL}/docs`

---

## Health

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 서버 상태 확인 |

**Response:**
```json
{
  "status": "ok"
}
```

---

## /stock — 종목 시세·차트

### 분봉 조회

| Method | Path | 필수 파라미터 | 설명 |
|--------|------|------------|------|
| GET | `/stock/{iscd}/minute-chart` | `date` | 분봉 조회 (당일 전체, DB 캐시 자동 처리) |

**Input:**
- `iscd`: 종목코드 (ex. `005930`)
- `date`: 조회 날짜 `YYYYMMDD`

**Example:**
`GET /stock/005930/minute-chart?date=20260102`

**Output:**
```json
[
  {
    "stock_code": "005930",
    "trade_date": "20260102",
    "trade_time": "090100",
    "open_price": 75000,
    "high_price": 75200,
    "low_price": 74900,
    "close_price": 75100,
    "volume": 120000,
    "cumul_amount": 9000000000
  }
]
```

### OHLCV (일/주/월/년봉)

| Method | Path | 필수 파라미터 | 설명 |
|--------|------|------------|------|
| GET | `/stock/{iscd}/ohlcv` | `start`, `end` | 기간별 OHLCV |
| GET | `/stock/{iscd}/ohlcv/all` | — | 전 기간 OHLCV (페이지네이션 자동) |

**Input:**
- `period`: `D`(일), `W`(주), `M`(월), `Y`(년)
- `save`: `true` (기본값, DB 저장 여부)

**Example:**
`GET /stock/005930/ohlcv?start=20260101&end=20260113&period=D&save=true`

**Output:**
```json
[
  {
    "date": "20260113",
    "open": 75000,
    "high": 76000,
    "low": 74500,
    "close": 75500,
    "volume": 15000000,
    "amount": 1130000000000,
    "change_sign": "2",
    "change_val": 500
  }
]
```

### 현재가 / 호가 / 투자자

| Method | Path | 설명 |
|--------|------|------|
| GET | `/stock/{iscd}/current` | 현재가 스냅샷 |
| GET | `/stock/{iscd}/orderbook` | 호가 / 예상체결 |
| GET | `/stock/{iscd}/investor` | 투자자별 매매동향 |

**Example:**
`GET /stock/005930/current`

**Current Output:**
```json
{
  "current": 75500,
  "open": 75000,
  "high": 76000,
  "low": 74500,
  "change_val": 500,
  "change_rate": 0.67,
  "volume": 15000000,
  "market_cap": 450000000000000,
  "per": 15.2,
  "pbr": 1.1,
  "foreign_ratio": 52.5
}
```

---

## /account — 계좌

### 주식 잔고 조회

| Method | Path | 설명 |
|--------|------|------|
| GET | `/account/balance` | 주식 잔고 조회 |

**Output:**
```json
{
  "summary": {
    "deposit": 10000000,
    "total_eval": 25000000,
    "total_profit": 5000000
  },
  "stocks": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "quantity": 100,
      "avg_price": 70000,
      "current_price": 75500,
      "profit_rate": 7.86
    }
  ]
}
```

### 일별 주문체결 조회

| Method | Path | 설명 |
|--------|------|------|
| GET | `/account/daily-ccld` | 일별 주문체결 조회 |

**Input:**
- `start_dt`: 시작일 `YYYYMMDD` (기본: 오늘)
- `end_dt`: 종료일 `YYYYMMDD` (기본: 오늘)

**Output:**
```json
[
  {
    "order_no": "0000123456",
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "side": "매수",
    "order_qty": 10,
    "filled_qty": 10,
    "avg_price": 75000.0,
    "total_amount": 750000
  }
]
```

---

## /ranking — 순위

### 등락률 / 거래량 / 외국인·기관

| Category | Path | sort 파라미터 |
|----------|------|--------------|
| 등락률 | `/ranking/fluctuation` | `0`:상승률, `1`:하락률, `2`:시가대비상승, `3`:시가대비하락 |
| 거래량 | `/ranking/volume` | `0`:거래량, `1`:거래대금 |
| 외국인 순매수 | `/ranking/foreign` | `0`:수량, `1`:금액 |
| 기관 순매수 | `/ranking/institution` | `0`:수량, `1`:금액 |

**Volume Ranking Example:**
`GET /ranking/volume?sort=1` (거래대금 순위)

**Output (VolumeRankRow):**
```json
[
  {
    "rank": 1,
    "stock_code": "008350",
    "stock_name": "남선알미늄",
    "price": 3170,
    "change_rate": 15.5,
    "volume": 115066357,
    "trade_value": 368656346078
  }
]
```

**NetBuy Ranking Output (NetBuyRankRow):**
```json
[
  {
    "rank": 1,
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "price": 75000,
    "change_rate": 0.67,
    "net_buy_qty": 1353000,
    "net_buy_amount": 101475000000
  }
]
```

---

## 자주 쓰는 종목코드

| 코드 | 종목명 |
|------|--------|
| `005930` | 삼성전자 |
| `000660` | SK하이닉스 |
| `035420` | NAVER |
| `035720` | 카카오 |
| `005380` | 현대차 |
| `051910` | LG화학 |
