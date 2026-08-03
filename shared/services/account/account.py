"""계좌 잔고/체결 조회"""
import logging
import requests

from datetime import datetime

from shared.models.stock import (
    KisCommonHeader,
    BalanceRequest, BalanceResponse,
    DailyCcldRequest, DailyCcldResponse,
)
from shared.config import APP_KEY, APP_SECRET, CANO, ACNT_PRDT_CD, ENV_DV
from shared.kis_auth import DEMO_BASE_URL, REAL_BASE_URL, get_valid_token_for

_BASE_URL_BY_ENV = {"real": REAL_BASE_URL, "demo": DEMO_BASE_URL}

# 계좌 TR은 모의투자에서 앞자리가 T→V로 바뀐다. 실전 TR을 그대로 보내면 KIS가
# EGW02006 "모의투자 TR 이 아닙니다"로 거부한다 (요청 파라미터는 양쪽이 같다).
_TR_BALANCE = {"real": "TTTC8434R", "demo": "VTTC8434R"}
_TR_DAILY_CCLD = {"real": "TTTC0081R", "demo": "VTTC0081R"}

# "해당 앱키는 모의투자용 앱키가 아닙니다" — 실전 앱키로 모의 도메인의 계좌 TR을
# 부를 때 온다. 시세 TR은 같은 앱키로도 통과하기 때문에 계좌 탭에서만 터진다.
_NOT_DEMO_APPKEY = "EGW02007"

_TIMEOUT = 10


def _base_url(env: str) -> str:
    return _BASE_URL_BY_ENV.get(env, DEMO_BASE_URL)


def _header(token: str, tr_id: str) -> dict:
    return KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id=tr_id,
    ).to_dict()


def _request(path: str, tr_table: dict, params: dict, env: str, access_token: str = None) -> dict:
    """계좌 TR 1회 호출 — KIS 응답 본문을 그대로 dict로 돌려준다.

    KIS는 거부 응답에도 HTTP 500과 함께 rt_cd/msg_cd/msg1을 담아 준다. 여기서
    raise_for_status()로 끊어 버리면 그 메시지가 사라지고 화면에는 원인 없는
    "internal error"만 남는다. 상태 코드가 아니라 본문으로 성패를 판단한다.
    """
    token = access_token or get_valid_token_for(env)
    if not token:
        raise RuntimeError(f"KIS 토큰 발급 실패 (env={env})")

    res = requests.get(
        f"{_base_url(env)}{path}",
        headers=_header(token, tr_table[env]),
        params=params,
        timeout=_TIMEOUT,
    )
    try:
        return res.json()
    except ValueError:
        raise RuntimeError(
            f"KIS 응답을 해석할 수 없습니다 [{res.status_code}] {res.text[:200]}"
        )


def _call(path: str, tr_table: dict, params: dict, access_token: str = None) -> dict:
    """KIS_ENV로 부르고, 앱키가 그 도메인 것이 아니면 실전 도메인으로 한 번 더.

    KIS_ENV=demo인데 .env의 앱키·계좌가 실전이면 모의 도메인은 EGW02007로 계좌
    조회를 거부한다. 그 조합에서 잔고를 볼 수 있는 곳은 실전 도메인뿐이고 이 경로는
    조회 전용이므로, 주문 경로(KIS_ENV)는 건드리지 않고 여기서만 실전으로 넘어간다.
    """
    body = _request(path, tr_table, params, ENV_DV, access_token)
    if body.get("msg_cd") == _NOT_DEMO_APPKEY and ENV_DV != "real":
        logging.warning(
            f"모의 도메인이 앱키를 거부({_NOT_DEMO_APPKEY}) — 계좌 조회를 실전 도메인으로 재시도"
        )
        # 재시도 토큰은 실전 도메인 것이어야 한다 (넘겨받은 토큰은 KIS_ENV 도메인용)
        body = _request(path, tr_table, params, "real")
    return body


def get_balance(access_token: str = None) -> BalanceResponse:
    """주식 잔고 조회"""
    # 예전에는 TTTC8494R(주식잔고조회_실현손익)이 박혀 있었다. 그 TR은 엔드포인트가
    # inquire-balance-rlz-pl로 따로 있고 모의투자에도 없어서, 이 경로에서는 맞지 않는다.
    req = BalanceRequest(CANO=CANO, ACNT_PRDT_CD=ACNT_PRDT_CD)
    body = _call(
        "/uapi/domestic-stock/v1/trading/inquire-balance",
        _TR_BALANCE,
        req.model_dump(),
        access_token,
    )
    return BalanceResponse(**body)


def get_daily_ccld(start_dt: str = None, end_dt: str = None, access_token: str = None) -> DailyCcldResponse:
    """주식 일별 주문체결 조회"""
    today = datetime.now().strftime("%Y%m%d")

    req = DailyCcldRequest(
        CANO=CANO,
        ACNT_PRDT_CD=ACNT_PRDT_CD,
        INQR_STRT_DT=start_dt or today,
        INQR_END_DT=end_dt or today,
    )
    body = _call(
        "/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
        _TR_DAILY_CCLD,
        req.model_dump(),
        access_token,
    )
    return DailyCcldResponse(**body)
