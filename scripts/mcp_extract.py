"""KIS MCP에서 API 정보 추출"""
import requests
import json
import re

BASE = 'http://localhost:8081/mcp'
HEADERS = {'Accept': 'application/json, text/event-stream', 'Content-Type': 'application/json'}


def mcp_session():
    r = requests.post(BASE, headers=HEADERS, json={
        'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
        'params': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'claude', 'version': '1.0'}}
    }, stream=True)
    sid = r.headers.get('mcp-session-id')
    requests.post(BASE, headers={**HEADERS, 'mcp-session-id': sid}, json={
        'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {}
    }, stream=True)
    return sid


def search_fn(sid, fn):
    h = {**HEADERS, 'mcp-session-id': sid}
    r = requests.post(BASE, headers=h, json={
        'jsonrpc': '2.0', 'id': 10, 'method': 'tools/call',
        'params': {'name': 'search_domestic_stock_api', 'arguments': {'function_name': fn, 'query': fn}}
    }, stream=True)
    for line in r.iter_lines():
        if line and line.startswith(b'data: '):
            d = json.loads(line[6:])
            return json.loads(d['result']['content'][0]['text'])


def read_src_raw(sid, url):
    h = {**HEADERS, 'mcp-session-id': sid}
    r = requests.post(BASE, headers=h, json={
        'jsonrpc': '2.0', 'id': 11, 'method': 'tools/call',
        'params': {'name': 'read_source_code', 'arguments': {'url_main': url}}
    }, stream=True)
    for line in r.iter_lines():
        if line and line.startswith(b'data: '):
            d = json.loads(line[6:])
            return d['result']['content'][0]['text']


def extract_src(raw):
    parsed = json.loads(raw)
    content_str = parsed['results']['main']['content']
    m = re.search(r"content='(.*?)',\s*uri=", content_str, re.DOTALL)
    if not m:
        m = re.search(r"content='(.*?)'\\]$", content_str, re.DOTALL)
    if m:
        src = m.group(1)
        src = src.replace('\\n', '\n')
        src = src.replace("\\'", "'")
        return src
    return content_str


if __name__ == '__main__':
    sid = mcp_session()
    targets = [
        'finance_balance_sheet',
        'finance_income_statement',
        'finance_financial_ratio',
        'finance_profit_ratio',
        'finance_stability_ratio',
        'finance_growth_ratio',
        'search_stock_info',
        'chk_holiday',
        'estimate_perform',
        'ksdinfo_dividend',
    ]

    for fn in targets:
        res = search_fn(sid, fn)
        if not res.get('results'):
            print(f"{fn}: NOT FOUND")
            continue
        url = res['results'][0]['url_main']
        raw = read_src_raw(sid, url)
        src = extract_src(raw)
        api_url = re.search(r'API_URL\s*=\s*"([^"]+)"', src)
        tr_id = re.search(r'tr_id\s*=\s*"([A-Z0-9]+)"', src)
        params = re.findall(r'"([A-Z][A-Z_0-9]{2,})"\s*:', src)
        params_uniq = list(dict.fromkeys(params))[:12]
        print(f"{fn}:")
        print(f"  url:    {api_url.group(1) if api_url else '?'}")
        print(f"  tr_id:  {tr_id.group(1) if tr_id else '?'}")
        print(f"  params: {params_uniq}")
        print()
