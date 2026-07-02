"""수집용 KIS 클라이언트.

단일 앱키 환경에서는 shared.kis_auth 로의 얇은 위임이지만, 향후 수집 전용
앱키/레이트리밋을 분리하기 위한 지점이다. (trader 와 앱키를 분리할 때 여기서 관리)
"""
from typing import Optional

from shared.kis_auth import get_valid_token


class CollectorKisClient:
    """수집 유닛용 토큰 제공자."""

    def token(self) -> Optional[str]:
        return get_valid_token()


collector_client = CollectorKisClient()
