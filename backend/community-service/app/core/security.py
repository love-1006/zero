import logging

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger("community_auth")

_UNAUTHORIZED = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")
_FORBIDDEN = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")


class UserIdentity(BaseModel):
    user_id: int
    role: str


def get_current_user_from_token(token: str) -> UserIdentity:
    try:
        # algorithms=["HS256"] is an explicit allowlist — PyJWT will not honor
        # an "alg": "none" or other algorithm smuggled into the token header.
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        logger.warning("auth denied: reason=invalid_or_expired_token")
        raise _UNAUTHORIZED from None

    user_id = int(payload["sub"])
    role = str(payload.get("role", "user"))
    logger.info("auth success: user_id=%s role=%s", user_id, role)
    return UserIdentity(user_id=user_id, role=role)


def get_current_admin_from_token(token: str) -> UserIdentity:
    """공지사항 쓰기/수정/삭제는 Admin Service를 통해서만 열어주는 게 자연스럽다
    (community-service.md, SC-0102 관리자 권한 분리와 일치) — 같은 role 클레임을
    admin-service와 동일하게 검사한다."""
    user = get_current_user_from_token(token)
    if user.role != "admin":
        logger.warning("authorization denied: reason=insufficient_role user_id=%s role=%s", user.user_id, user.role)
        raise _FORBIDDEN
    return user
