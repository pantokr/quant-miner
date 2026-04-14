"""계좌 잔고/체결 조회"""
import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

from models.stock import (
    KisCommonHeader,
    BalanceRequest, BalanceResponse,
    DailyCcldRequest, DailyCcldResponse,
)
from services.auth import APP_KEY, APP_SECRET, BASE_URL, ENV_DV

load_dotenv()

CANO = os.getenv("KIS_CANO", "")
ACNT_PRDT_CD = os.getenv("KIS_ACNT_PRDT_CD", "01")


def get_balance(access_token: str) -> BalanceResponse:
    """주식 잔고 조회"""
    tr_id = "TTTC8434R" if ENV_DV == "real" else "VTTC8434R"
    header = KisCommonHeader(
        authorization=f"Bearer {access_token}",
        appkey=APP_KEY,
        appsecret=APP_SECRET,
        tr_id=tr_id,
    )
    req = BalanceRequest(CANO=CANO, ACNT_PRDT_CD=ACNT_PRDT_CD)

    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance",
        headers=header.to_dict(),
        params=req.model_dump(),
    )
    res.raise_for_status()
    return BalanceResponse(**res.json())


def get_daily_ccld(access_token: str, start_dt: str = None, end_dt: str = None) -> DailyCcldResponse:
    """주식 일별 주문체결 조회"""
    today = datetime.now().strftime("%Y%m%d")
    tr_id = "TTTC0081R" if ENV_DV == "real" else "VTTC0081R"
    header = KisCommonHeader(
        authorization=f"Bearer {access_token}",
        appkey=APP_KEY,
        appsecret=APP_SECRET,
        tr_id=tr_id,
    )
    req = DailyCcldRequest(
        CANO=CANO,
        ACNT_PRDT_CD=ACNT_PRDT_CD,
        INQR_STRT_DT=start_dt or today,
        INQR_END_DT=end_dt or today,
    )

    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
        headers=header.to_dict(),
        params=req.model_dump(),
    )
    res.raise_for_status()
    return DailyCcldResponse(**res.json())
