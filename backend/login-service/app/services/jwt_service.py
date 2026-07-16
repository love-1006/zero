import time

import jwt

from app.core.config import settings


def create_access_token(user_id: int, provider: str, nickname: str, role: str = "user") -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        # int 형태로도 넣어둔다 — product/ingredients/diet-service가
        # payload["user_id"]를 그대로 읽는 컨벤션이라, sub만 있으면 그
        # 서비스들에서 KeyError가 난다.
        "user_id": user_id,
        "provider": provider,
        "nickname": nickname,
        "role": role,
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_user_id(token: str) -> int:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    return int(payload["sub"])


def decode_payload(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def refresh_token(payload: dict) -> str:
    """검증된 기존 payload의 클레임(sub/user_id/provider/nickname/role)은
    그대로 유지하고 iat/exp만 새로 발급한다 — 슬라이딩 세션(요청마다 만료
    시각 연장)용."""
    now = int(time.time())
    new_payload = {**payload, "iat": now, "exp": now + settings.jwt_expire_minutes * 60}
    return jwt.encode(new_payload, settings.jwt_secret, algorithm="HS256")
