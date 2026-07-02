"""API 인증 (스텁).

TODO: 실제 JWT 발급/검증 구현. 현재는 구조만 제공한다.
- 환경변수 API_JWT_SECRET 로 서명(미설정 시 개발용 기본값)
- verify_token 을 FastAPI Depends 로 보호 라우트에 부착
"""
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.getenv("API_JWT_SECRET", "dev-secret-change-me")
_bearer = HTTPBearer(auto_error=False)


def verify_token(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    """Bearer 토큰 검증 의존성 (스텁).

    TODO: PyJWT 로 서명/만료 검증. 지금은 토큰 존재 여부만 확인한다.
    보호가 필요한 라우트에 `Depends(verify_token)` 로 부착.
    """
    if cred is None or not cred.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다",
        )
    # TODO: jwt.decode(cred.credentials, JWT_SECRET, algorithms=["HS256"])
    return {"token": cred.credentials}
