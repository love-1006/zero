import logging

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger("main_auth")

_UNAUTHORIZED = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")


class UserIdentity(BaseModel):
    user_id: int
    nickname: str


def get_current_user_from_token(token: str) -> UserIdentity:
    try:
        # algorithms=["HS256"] is an explicit allowlist — PyJWT will not honor
        # an "alg": "none" or other algorithm smuggled into the token header.
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        logger.warning("user auth denied: reason=invalid_or_expired_token")
        raise _UNAUTHORIZED from None

    user_id = int(payload["sub"])
    nickname = str(payload.get("nickname", ""))
    logger.info("user auth success: user_id=%s", user_id)
    return UserIdentity(user_id=user_id, nickname=nickname)
