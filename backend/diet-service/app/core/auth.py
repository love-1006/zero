import logging

import jwt
from fastapi import HTTPException, Query

from app.core.config import settings

logger = logging.getLogger("diet_service.auth")

_ALLOWED_ALGORITHMS = {"HS256"}


def get_current_user(usr: str = Query(..., description="JWT 토큰")) -> dict:
    try:
        payload = jwt.decode(
            usr,
            settings.jwt_secret,
            algorithms=list(_ALLOWED_ALGORITHMS),
        )
    except jwt.ExpiredSignatureError:
        # 토큰 값 자체는 절대 로그에 남기지 않는다 (민감정보 — ASVS V16.4.1).
        logger.warning("auth: expired token")
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        logger.warning("auth: invalid token")
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    return payload
