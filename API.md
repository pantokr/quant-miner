
# Quant Miner API 엔드포인트

베이스 URL: `http://158.180.79.14:8000`  
로컬 URL: `http://localhost:8000`  
Swagger UI: `{BASE_URL}/docs`

---

## Health

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 서버 상태 확인 |

```
GET /health
```

---

## /stock — 종목 시세·차트

### 분봉

| Method | Path | 필수 파라미터 | 설명 |
|--------|------|------------|------|
| GET | `/stock/{iscd}/minute-chart` | `start`, `end` | 분봉 조회 (DB 캐시 자동 처리) |

```
GET /stock/005930/minute-chart?start=20260102+090000&end=20260102+153000
```

### OHLCV (일/주/월/년봉)

| Method | Path | 필수 파라미터 | 설명 |
|--------|------|------------|------|
| GET | `/stock/{iscd}/ohlcv` | `start`, `end` | 기간별 OHLCV |
| GET | `/stock/{iscd}/ohlcv/all` | — | 전 기간 OHLCV (페이지네이션 자동) |

```
GET /stock/005930/ohlcv?start=20260101&end=20260113&period=D&save=true
GET /stock/005930/ohlcv/all?start=19900101&period=D&save=true
```

`period`: `D`(일) `W`(주) `M`(월) `Y`(년)

### 현재가 / 호가 / 투자자

| Method | Path | 설명 |
|--------|------|------|
| GET | `/stock/{iscd}/current` | 현재가 스냅샷 |
| GET | `/stock/{iscd}/orderbook` | 호가 / 예상체결 |
| GET | `/stock/{iscd}/investor` | 투자자별 매매동향 |

```
GET /stock/005930/current
GET /stock/005930/orderbook
GET /stock/005930/investor
```

### 공매도 / 신용잔고 (실전투자 전용)

| Method | Path | 필수 파라미터 | 설명 |
|--------|------|------------|------|
| GET | `/stock/{iscd}/short-sell` | `start`, `end` | 공매도 현황 |
| GET | `/stock/{iscd}/credit` | `start`, `end` | 신용잔고 |

```
GET /stock/005930/short-sell?start=20260102&end=20260113
GET /stock/005930/credit?start=20260102&end=20260113
```

---

## /account — 계좌

| Method | Path | 설명 |
|--------|------|------|
| GET | `/account/balance` | 주식 잔고 조회 |
| GET | `/account/daily-ccld` | 일별 주문체결 조회 |

```
GET /account/balance
GET /account/daily-ccld?start_dt=20260102&end_dt=20260113
```

---

## /ranking — 순위

### 등락률

| Method | Path | sort 값 | 설명 |
|--------|------|---------|------|
| GET | `/ranking/fluctuation` | `0` 상승률 (기본) | 등락률 순위 |
| | | `1` 하락률 | |
| | | `2` 시가대비 상승 | |
| | | `3` 시가대비 하락 | |

```
GET /ranking/fluctuation?sort=0
```

### 거래량

| Method | Path | sort 값 | 설명 |
|--------|------|---------|------|
| GET | `/ranking/volume` | `0` 거래량 (기본) | 거래량/거래대금 순위 |
| | | `1` 거래대금 | |

```
GET /ranking/volume?sort=0
```

### 외국인 / 기관 순매수

| Method | Path | sort 값 | 설명 |
|--------|------|---------|------|
| GET | `/ranking/foreign` | `0` 순매수수량 (기본) | 외국인 순매수 순위 |
| | | `1` 순매수대금 | |
| GET | `/ranking/institution` | `0` 순매수수량 (기본) | 기관 순매수 순위 |
| | | `1` 순매수대금 | |

```
GET /ranking/foreign?sort=0
GET /ranking/institution?sort=1
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
