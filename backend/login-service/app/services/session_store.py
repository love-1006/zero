from app.core.config import settings
from app.core.redis_client import redis_client

# Not a real per-user session mechanism — still just a single "last active
# token" slot for local/manual testing convenience (see auth.py's `link`
# fallback), now backed by Redis instead of a process-local global so it
# survives restarts and is shared across instances.
_KEY = "login-service:session:active_token"


async def set_active_token(token: str) -> None:
    await redis_client.set(_KEY, token, ex=settings.jwt_expire_minutes * 60)


async def get_active_token() -> str | None:
    return await redis_client.get(_KEY)
