"""KIS MCP의 chk_*.py에서 COLUMN_MAPPING(전체 응답 필드) 수집 → JSON 저장.

response.py 모델을 오리지날 전체 필드로 재생성하기 위한 소스 데이터 수집용.
"""
import requests
import json
import re
import sys

BASE = 'http://localhost:8081/mcp'
HEADERS = {'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json'}

# 검색 함수명 → response.py에서 대응하는 모델 (참고용 라벨)
TARGETS = [
    ('inquire_balance', 'BalanceResponse'),
    ('inquire_daily_ccld', 'DailyCcldResponse'),
    ('inquire_time_itemchartprice', 'MinuteChartResponse'),
    ('inquire_time_dailychartprice', 'MinuteDailyChartResponse'),
    ('inquire_daily_itemchartprice', 'OhlcvResponse'),
    ('inquire_price', 'CurrentPriceResponse'),
    ('fluctuation', 'FluctuationRankResponse'),
    ('volume_rank', 'VolumeRankResponse'),
    ('foreign_institution_total', 'ForeignInstRankResponse'),
    ('inquire_investor', 'InvestorResponse'),
    ('inquire_asking_price_exp_ccn', 'OrderBookResponse'),
    ('daily_short_sale', 'ShortSellResponse'),
    ('daily_credit_balance', 'CreditResponse'),
    ('finance_balance_sheet', 'FinanceResponse:balance_sheet'),
    ('finance_income_statement', 'FinanceResponse:income_statement'),
    ('finance_financial_ratio', 'FinanceResponse:financial_ratio'),
    ('finance_profit_ratio', 'FinanceResponse:profit_ratio'),
    ('finance_stability_ratio', 'FinanceResponse:stability_ratio'),
    ('finance_growth_ratio', 'FinanceResponse:growth_ratio'),
    ('search_stock_info', 'StockInfoResponse'),
    ('chk_holiday', 'HolidayResponse'),
    ('ksdinfo_dividend', 'DividendResponse'),
    ('estimate_perform', 'EstimateResponse'),
]


def mcp_session():
    r = requests.post(BASE, headers=HEADERS, json={
        'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
        'params': {'protocolVersion': '2024-11-05', 'capabilities': {},
                   'clientInfo': {'name': 'claude', 'version': '1.0'}}
    }, stream=True)
    sid = r.headers.get('mcp-session-id')
    requests.post(BASE, headers={**HEADERS, 'mcp-session-id': sid}, json={
        'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {}
    }, stream=True)
    return sid


def call(sid, name, args):
    r = requests.post(BASE, headers={**HEADERS, 'mcp-session-id': sid}, json={
        'jsonrpc': '2.0', 'id': 10, 'method': 'tools/call',
        'params': {'name': name, 'arguments': args}
    }, stream=True)
    for line in r.iter_lines():
        if line and line.startswith(b'data: '):
            return json.loads(line[6:])


def search(sid, fn):
    res = call(sid, 'search_domestic_stock_api', {'function_name': fn, 'query': fn})
    return json.loads(res['result']['content'][0]['text'])


def read_src(sid, url_main, url_chk):
    res = call(sid, 'read_source_code', {'url_main': url_main, 'url_chk': url_chk})
    return json.loads(res['result']['content'][0]['text'])


def unwrap(content):
    m = re.search(r"content='(.*?)',\s*(?:uri=|mime)", content, re.DOTALL)
    src = m.group(1) if m else content
    return src.replace('\\n', '\n').replace("\\'", "'")


def parse_column_mapping(src):
    """COLUMN_MAPPING = { 'field': '한글', ... } 블록을 파싱."""
    m = re.search(r"COLUMN_MAPPING\s*=\s*\{(.*?)\n\}", src, re.DOTALL)
    if not m:
        return {}
    body = m.group(1)
    # 따옴표는 작은/큰 둘 다 대응
    pairs = re.findall(r"""['"]([a-zA-Z0-9_]+)['"]\s*:\s*['"]([^'"]*)['"]""", body)
    return {k: v for k, v in pairs}


if __name__ == '__main__':
    sid = mcp_session()
    out = {}
    for fn, label in TARGETS:
        try:
            sres = search(sid, fn)
            results = sres.get('results') or []
            # 정확히 일치하는 function_name 우선
            pick = next((r for r in results if r.get('function_name') == fn), None)
            if pick is None and results:
                pick = results[0]
            if not pick:
                out[label] = {'fn': fn, 'error': 'not found', 'matches': [r.get('function_name') for r in results]}
                print(f'[MISS] {fn} -> {label}: no results')
                continue
            url_main = pick.get('url_main', '')
            url_chk = pick.get('url_chk', '')
            srcs = read_src(sid, url_main, url_chk)
            chk = srcs['results'].get('check') or {}
            chk_src = unwrap(chk.get('content', '')) if chk else ''
            mapping = parse_column_mapping(chk_src)
            out[label] = {
                'fn': fn,
                'matched': pick.get('function_name'),
                'api_name': pick.get('api_name'),
                'url_main': url_main,
                'fields': mapping,
            }
            print(f'[OK]   {fn:32s} -> {label:34s} fields={len(mapping)}')
        except Exception as e:
            out[label] = {'fn': fn, 'error': repr(e)}
            print(f'[ERR]  {fn} -> {label}: {e!r}')

    with open(r'c:\workspaces\quant-miner\scripts\_mappings.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print('\nSaved scripts/_mappings.json')
