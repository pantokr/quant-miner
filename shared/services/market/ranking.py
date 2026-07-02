"""주식 순위 조회 서비스"""
import requests
import logging
from typing import List

from shared.models.stock import (
    KisCommonHeader,
    FluctuationRankRequest, FluctuationRankItem, FluctuationRankResponse,
    VolumeRankRequest, VolumeRankItem, VolumeRankResponse,
    ForeignInstRankRequest, ForeignInstRankItem, ForeignInstRankResponse,
)
from shared.kis_auth import APP_KEY, APP_SECRET, BASE_URL
from shared.kis_auth import get_valid_token


def _header(token: str, tr_id: str) -> dict:
    return KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id=tr_id,
    ).to_dict()


def get_fluctuation_rank(sort: str = "0", access_token: str = None) -> List[FluctuationRankItem]:
    """
    등락률 순위 조회

    Args:
        sort: 0:상승률 1:하락률 2:시가대비상승 3:시가대비하락
    """
    token = access_token or get_valid_token()

    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/ranking/fluctuation",
        headers=_header(token, "FHPST01700000"),
        params=FluctuationRankRequest(
            FID_RANK_SORT_CLS_CODE=sort).model_dump(),
    )

    res.raise_for_status()
    result = FluctuationRankResponse(**res.json())
    if not result.is_success:
        logging.error(f"등락률순위 오류: {result.msg1}")
        return []
    return result.output


def get_volume_rank(sort: str = "0", access_token: str = None) -> List[VolumeRankItem]:
    """
    거래량/거래대금 순위 조회

    Args:
        sort: 0:거래량 1:거래대금
    """
    token = access_token or get_valid_token()

    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/volume-rank",
        headers=_header(token, "FHPST01710000"),
        params=VolumeRankRequest(FID_BLNG_CLS_CODE=sort).model_dump(),
    )
    res.raise_for_status()
    result = VolumeRankResponse(**res.json())
    if not result.is_success:
        logging.error(f"거래량순위 오류: {result.msg1}")
        return []
    return result.output


def get_foreign_rank(sort: str = "0", access_token: str = None) -> List[ForeignInstRankItem]:
    """
    외국인 순매수 순위 조회 (가집계)

    Args:
        sort: 0:순매수수량 1:순매수대금
    """
    token = access_token or get_valid_token()

    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/foreign-institution-total",
        headers=_header(token, "FHPTJ04400000"),
        params={
            "FID_COND_MRKT_DIV_CODE": "V",
            "FID_COND_SCR_DIV_CODE": "16449",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": sort,
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_ETC_CLS_CODE": "1",
        },
    )
    res.raise_for_status()
    result = ForeignInstRankResponse(**res.json())
    if not result.is_success:
        logging.error(f"외국인순매수순위 오류: {result.msg1}")
        return []
    return result.output


def get_institution_rank(sort: str = "0", access_token: str = None) -> List[ForeignInstRankItem]:
    """
    기관 순매수 순위 조회 (가집계)

    Args:
        sort: 0:순매수수량 1:순매수대금
    """
    token = access_token or get_valid_token()

    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/foreign-institution-total",
        headers=_header(token, "FHPTJ04400000"),
        params={
            "FID_COND_MRKT_DIV_CODE": "V",
            "FID_COND_SCR_DIV_CODE": "16449",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": sort,
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_ETC_CLS_CODE": "2",
        },
    )
    res.raise_for_status()
    result = ForeignInstRankResponse(**res.json())
    if not result.is_success:
        logging.error(f"기관순매수순위 오류: {result.msg1}")
        return []
    return result.output
