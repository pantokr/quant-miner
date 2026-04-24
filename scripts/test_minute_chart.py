#!/usr/bin/env python3
"""
분봉 조회 API 테스트 스크립트
Q610075 종목의 2026-04-24 하루 전체 분봉 데이터를 조회합니다.
"""

import requests


def test_minute_chart():
    """분봉 조회 테스트"""
    iscd = "Q610075"
    date = "20260424"  # 오늘 날짜 (2026-04-24)
    url = f"http://127.0.0.1:8000/stock/{iscd}/minute-chart?date={date}"

    print(f"요청 URL: {url}")
    print("분봉 데이터 조회 중...")

    try:
        response = requests.get(url, timeout=30)
        print(f"응답 상태 코드: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"총 데이터 개수: {len(data)}")

            if data:
                print("\n처음 10개 데이터 샘플:")
                for i, item in enumerate(data[:10]):
                    print(f"{i+1}. 시간: {item.get('trade_time')}, "
                          f"시가: {item.get('open_price')}, "
                          f"고가: {item.get('high_price')}, "
                          f"저가: {item.get('low_price')}, "
                          f"종가: {item.get('close_price')}, "
                          f"거래량: {item.get('volume')}")

                if len(data) > 10:
                    print(f"\n... 및 {len(data) - 10}개 더 있습니다.")

                # 시간 범위 확인
                if data:
                    start_time = data[0]['trade_time']
                    end_time = data[-1]['trade_time']
                    print(f"\n시간 범위: {start_time} ~ {end_time}")
            else:
                print("데이터가 없습니다.")
        else:
            print(f"API 오류: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"요청 실패: {e}")


if __name__ == "__main__":
    test_minute_chart()
