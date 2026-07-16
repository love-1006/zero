import json
import secrets
from dataclasses import dataclass

from app.core.redis_client import redis_client

_STATE_TTL_SECONDS = 300
_KEY_PREFIX = "login-service:oauth-state:"


@dataclass
class StateEntry:
    link_user_id: int | None = None


async def create_state(link_user_id: int | None = None) -> str:
    state = secrets.token_urlsafe(24)
    payload = json.dumps({"link_user_id": link_user_id})
    await redis_client.set(f"{_KEY_PREFIX}{state}", payload, ex=_STATE_TTL_SECONDS)
    return state


async def verify_and_consume_state(state: str) -> StateEntry | None:
    # GETDEL: 원자적으로 읽고 즉시 삭제 — 같은 state를 두 번 쓰는 재사용(replay)
    # 공격을 막는다 (dict.pop()이 하던 것과 동일한 일회성 보장).
    raw = await redis_client.getdel(f"{_KEY_PREFIX}{state}")
    if raw is None:
        return None
    data = json.loads(raw)
    return StateEntry(link_user_id=data.get("link_user_id"))
