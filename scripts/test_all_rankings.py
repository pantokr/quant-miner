
from shared.services.market.ranking import (
    get_fluctuation_rank,
    get_volume_rank,
    get_foreign_rank,
    get_institution_rank
)
import logging
import sys
import os

# 현재 디렉토리를 path에 추가하여 모듈 로드 가능하게 함
sys.path.append(os.getcwd())


logging.basicConfig(level=logging.INFO)


def test_rankings():
    print("=== [1] 등락률 순위 테스트 (상승률) ===")
    try:
        results = get_fluctuation_rank(sort="0")
        print(f"조회 결과 개수: {len(results)}")
        if results:
            for item in results[:3]:
                print(
                    f"[{item.data_rank}] {item.hts_kor_isnm} ({item.mksc_shrn_iscd}) - 현재가: {item.stck_prpr}, 등락률: {item.prdy_ctrt}%")
    except Exception as e:
        print(f"오류 발생: {e}")

    print("\n=== [2] 거래량 순위 테스트 (거래량) ===")
    try:
        results = get_volume_rank(sort="0")
        print(f"조회 결과 개수: {len(results)}")
        if results:
            for item in results[:3]:
                print(
                    f"[{item.data_rank}] {item.hts_kor_isnm} ({item.mksc_shrn_iscd}) - 거래량: {item.acml_vol}")
    except Exception as e:
        print(f"오류 발생: {e}")

    print("\n=== [3] 외국인 순매수 순위 테스트 (수량) ===")
    try:
        results = get_foreign_rank(sort="0")
        print(f"조회 결과 개수: {len(results)}")
        if results:
            for item in results[:3]:
                print(
                    f"[{item.data_rank}] {item.hts_kor_isnm} ({item.mksc_shrn_iscd}) - 외국인순매수: {item.ntby_qty}")
    except Exception as e:
        print(f"오류 발생: {e}")

    print("\n=== [4] 기관 순매수 순위 테스트 (수량) ===")
    try:
        results = get_institution_rank(sort="0")
        print(f"조회 결과 개수: {len(results)}")
        if results:
            for item in results[:3]:
                print(
                    f"[{item.data_rank}] {item.hts_kor_isnm} ({item.mksc_shrn_iscd}) - 기관순매수: {item.ntby_qty}")
    except Exception as e:
        print(f"오류 발생: {e}")


if __name__ == "__main__":
    test_rankings()
