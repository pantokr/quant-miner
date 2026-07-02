from fastapi import APIRouter, Query, HTTPException
from typing import List

from shared.models.stock import FluctuationRankRow, VolumeRankRow, NetBuyRankRow
from shared.services.market.ranking import (
    get_fluctuation_rank,
    get_volume_rank,
    get_foreign_rank,
    get_institution_rank,
)

router = APIRouter(prefix="/ranking", tags=["ranking"])


@router.get("/fluctuation", response_model=List[FluctuationRankRow])
def fluctuation_rank(
    sort: str = Query("0", description="0:상승률 1:하락률 2:시가대비상승 3:시가대비하락"),
):
    """등락률 순위"""
    items = get_fluctuation_rank(sort=sort)
    if not items:
        raise HTTPException(status_code=502, detail="데이터 없음")
    return [
        FluctuationRankRow(
            rank=int(i.data_rank),
            stock_code=i.stck_shrn_iscd,
            stock_name=i.hts_kor_isnm,
            price=int(i.stck_prpr),
            change_rate=float(i.prdy_ctrt),
            volume=int(i.acml_vol),
            trade_value=int(i.acml_tr_pbmn or 0),
        )
        for i in items
    ]


@router.get("/volume", response_model=List[VolumeRankRow])
def volume_rank(
    sort: str = Query("0", description="0:거래량 1:거래대금"),
):
    """거래량/거래대금 순위"""
    items = get_volume_rank(sort=sort)
    if not items:
        raise HTTPException(status_code=502, detail="데이터 없음")
    return [
        VolumeRankRow(
            rank=int(i.data_rank),
            stock_code=i.mksc_shrn_iscd,
            stock_name=i.hts_kor_isnm,
            price=int(i.stck_prpr),
            change_rate=float(i.prdy_ctrt),
            volume=int(i.acml_vol),
            trade_value=int(i.acml_tr_pbmn),
        )
        for i in items
    ]


@router.get("/foreign", response_model=List[NetBuyRankRow])
def foreign_rank(
    sort: str = Query("0", description="0:순매수수량 1:순매수대금"),
):
    """외국인 순매수 순위"""
    items = get_foreign_rank(sort=sort)
    if not items:
        raise HTTPException(status_code=502, detail="데이터 없음")
    return [
        NetBuyRankRow(
            rank=idx + 1,
            stock_code=i.mksc_shrn_iscd,
            stock_name=i.hts_kor_isnm,
            price=int(i.stck_prpr),
            change_rate=float(i.prdy_ctrt),
            net_buy_qty=int(i.ntby_qty),
            net_buy_amount=int(i.ntby_pbmn),
        )
        for idx, i in enumerate(items)
    ]


@router.get("/institution", response_model=List[NetBuyRankRow])
def institution_rank(
    sort: str = Query("0", description="0:순매수수량 1:순매수대금"),
):
    """기관 순매수 순위"""
    items = get_institution_rank(sort=sort)
    if not items:
        raise HTTPException(status_code=502, detail="데이터 없음")
    return [
        NetBuyRankRow(
            rank=idx + 1,
            stock_code=i.mksc_shrn_iscd,
            stock_name=i.hts_kor_isnm,
            price=int(i.stck_prpr),
            change_rate=float(i.prdy_ctrt),
            net_buy_qty=int(i.ntby_qty),
            net_buy_amount=int(i.ntby_pbmn),
        )
        for idx, i in enumerate(items)
    ]
