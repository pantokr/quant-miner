import requests


def test_api_rankings():
    base_url = "http://localhost:8000/ranking"

    endpoints = [
        ("fluctuation", "등락률"),
        ("volume", "거래량"),
        ("foreign", "외국인 순매수"),
        ("institution", "기관 순매수")
    ]

    for path, name in endpoints:
        print(f"\n=== {name} API 테스트 ===")
        try:
            res = requests.get(f"{base_url}/{path}", params={"sort": "0"})
            res.raise_for_status()
            data = res.json()
            print(f"조회 결과 개수: {len(data)}")
            if data:
                for item in data[:3]:
                    rank = item.get("rank")
                    name = item.get("stock_name")
                    code = item.get("stock_code")
                    val = item.get("net_buy_qty") or item.get(
                        "volume") or item.get("change_rate")
                    print(f"[{rank}] {name} ({code}) - 값: {val}")
        except Exception as e:
            print(f"오류 발생: {e}")


if __name__ == "__main__":
    test_api_rankings()
