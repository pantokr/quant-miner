"""KIS MCP에서 API 응답 필드 추출"""
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


def read_chk_src(sid, url):
    h = {**HEADERS, 'mcp-session-id': sid}
    r = requests.post(BASE, headers=h, json={
        'jsonrpc': '2.0', 'id': 12, 'method': 'tools/call',
        'params': {'name': 'read_source_code', 'arguments': {'url_chk': url}}
    }, stream=True)
    for line in r.iter_lines():
        if line and line.startswith(b'data: '):
            d = json.loads(line[6:])
            return d['result']['content'][0]['text']


if __name__ == '__main__':
    sid = mcp_session()
    targets = [
        'finance_balance_sheet',
        'finance_income_statement',
        'finance_financial_ratio',
        'search_stock_info',
        'chk_holiday',
        'estimate_perform',
        'ksdinfo_dividend',
    ]

    for fn in targets:
        res = search_fn(sid, fn)
        if not res.get('results'):
            continue
        info = res['results'][0]
        url_main = info.get('url_main', '')
        url_chk = info.get('url_chk', '')

        raw = read_src_raw(sid, url_main)
        src = extract_src(raw)

        # Also check the chk file for output column names
        chk_raw = read_chk_src(sid, url_chk) if url_chk else ''
        chk_src = ''
        if chk_raw:
            try:
                chk_src = extract_src(chk_raw)
            except Exception:
                pass

        # Extract output field names from column references
        output_fields = re.findall(r"output\['([a-z_]+)'\]", src + chk_src)
        output_fields += re.findall(r'\.([a-z_]{3,})\b', src + chk_src)
        # Get unique lowercase field names that look like API fields
        unique_fields = list(dict.fromkeys([
            f for f in output_fields
            if len(f) > 3 and not f.startswith('get') and '_' in f
        ]))[:20]

        print(f"\n=== {fn} ===")
        print(f"  output fields: {unique_fields}")
        # Print the chk source for manual inspection
        if chk_src:
            print(f"  chk src preview: {chk_src[:800]}")
