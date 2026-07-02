
from shared.services.market.ranking import get_volume_rank
import logging
import sys
import os

# 현재 디렉토리를 path에 추가하여 모듈 로드 가능하게 함
sys.path.append(os.getcwd())


logging.basicConfig(level=logging.INFO)


def test_volume_rank():
    print("=== 거래량 순위 테스트 시작 (sort='0': 거래량) ===")
    try:
        results = get_volume_rank(sort="0")
        print(f"조회 결과 개수: {len(results)}")
        if results:
            for item in results[:5]:
                print(
                    f"[{item.data_rank}] {item.hts_kor_isnm} ({item.mksc_shrn_iscd}) - 현재가: {item.stck_prpr}, 거래량: {item.acml_vol}")
        else:
            print("결과가 없습니다. (장 종료 후 또는 API 오류)")
    except Exception as e:
        print(f"오류 발생: {e}")

    print("\n=== 거래대금 순위 테스트 시작 (sort='1': 거래대금) ===")
    try:
        results = get_volume_rank(sort="1")
        print(f"조회 결과 개수: {len(results)}")
        if results:
            for item in results[:5]:
                print(
                    f"[{item.data_rank}] {item.hts_kor_isnm} ({item.mksc_shrn_iscd}) - 현재가: {item.stck_prpr}, 거래대금: {item.acml_tr_pbmn}")
        else:
            print("결과가 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")


if __name__ == "__main__":
    test_volume_rank()
