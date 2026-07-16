import logging
import time

import jwt
from fastapi import Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger("admin_auth")

_bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 인증 정보입니다.")
_FORBIDDEN = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")


class AdminIdentity(BaseModel):
    user_id: int
    login_id: str


async def get_current_admin(
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AdminIdentity:
    if credentials is None:
        logger.warning("admin auth denied: reason=missing_token")
        raise _UNAUTHORIZED

    try:
        # algorithms=["HS256"] is an explicit allowlist — PyJWT will not honor
        # an "alg": "none" or other algorithm smuggled into the token header.
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        logger.warning("admin auth denied: reason=invalid_or_expired_token")
        raise _UNAUTHORIZED from None

    if payload.get("role") != "admin":
        logger.warning("admin auth denied: reason=insufficient_role user_id=%s", payload.get("sub"))
        raise _FORBIDDEN

    user_id = int(payload["sub"])
    login_id = str(payload.get("nickname", ""))
    logger.info("admin auth success: user_id=%s", user_id)

    # 슬라이딩 세션 — 같은 시크릿으로 클레임은 유지한 채 만료시각만 연장해
    # 재서명, 응답 헤더로 내려준다. 프론트는 이 헤더가 있으면 토큰을 교체한다.
    now = int(time.time())
    refreshed_payload = {**payload, "iat": now, "exp": now + settings.jwt_expire_minutes * 60}
    response.headers["X-Refreshed-Token"] = jwt.encode(refreshed_payload, settings.jwt_secret, algorithm="HS256")

    return AdminIdentity(user_id=user_id, login_id=login_id)
