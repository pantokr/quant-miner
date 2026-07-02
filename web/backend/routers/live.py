"""실시간 데이터 라우터 (api 게이트웨이 중계).

DB에 저장하지 않는 실시간 데이터(현재가·호가·랭킹·잔고·체결·공매도·신용)는
api 게이트웨이로 중계한다. backend는 KIS를 직접 호출하지 않는다.
프론트가 쓰는 경로를 그대로 노출하고, 쿼리 파라미터를 그대로 전달한다.
"""
from fastapi import APIRouter, Request

from web.backend.gateway import proxy_get

router = APIRouter(tags=["live (proxy→api)"])


def _q(request: Request) -> dict:
    return dict(request.query_params)


# ── 종목 실시간 ────────────────────────────────────────────
@router.get("/stock/{iscd}/current")
def current(iscd: str, request: Request):
    return proxy_get(f"/stock/{iscd}/current", _q(request))


@router.get("/stock/{iscd}/orderbook")
def orderbook(iscd: str, request: Request):
    return proxy_get(f"/stock/{iscd}/orderbook", _q(request))


@router.get("/stock/{iscd}/short-sell")
def short_sell(iscd: str, request: Request):
    return proxy_get(f"/stock/{iscd}/short-sell", _q(request))


@router.get("/stock/{iscd}/credit")
def credit(iscd: str, request: Request):
    return proxy_get(f"/stock/{iscd}/credit", _q(request))


# ── 계좌 ───────────────────────────────────────────────────
@router.get("/account/balance")
def balance(request: Request):
    return proxy_get("/account/balance", _q(request))


@router.get("/account/daily-ccld")
def daily_ccld(request: Request):
    return proxy_get("/account/daily-ccld", _q(request))


# ── 랭킹 ───────────────────────────────────────────────────
@router.get("/ranking/fluctuation")
def rank_fluctuation(request: Request):
    return proxy_get("/ranking/fluctuation", _q(request))


@router.get("/ranking/volume")
def rank_volume(request: Request):
    return proxy_get("/ranking/volume", _q(request))


@router.get("/ranking/foreign")
def rank_foreign(request: Request):
    return proxy_get("/ranking/foreign", _q(request))


@router.get("/ranking/institution")
def rank_institution(request: Request):
    return proxy_get("/ranking/institution", _q(request))
