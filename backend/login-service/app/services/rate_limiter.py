import secrets
import time

from app.core.redis_client import redis_client

_WINDOW_SECONDS = 60.0
_KEY_PREFIX = "login-service:ratelimit:"


async def hit(key: str, max_attempts: int, window_seconds: float = _WINDOW_SECONDS) -> bool:
    """Record an attempt under `key` and report whether it should be blocked.

    Sliding-window log via a Redis ZSET: each attempt is a member scored by
    its timestamp; members older than the window are trimmed before counting.
    There's a small check-then-add race under heavy concurrent traffic on the
    same key (two requests can both pass the count check before either adds
    its member) — acceptable here since this is anti-automation throttling,
    not a hard security boundary.
    """
    redis_key = f"{_KEY_PREFIX}{key}"
    now = time.time()
    window_start = now - window_seconds

    await redis_client.zremrangebyscore(redis_key, 0, window_start)
    current_count = await redis_client.zcard(redis_key)

    if current_count >= max_attempts:
        return True

    # Timestamp alone can collide under rapid-fire requests on the same key —
    # pair it with a random suffix so ZADD never silently dedupes two hits.
    member = f"{now}:{secrets.token_hex(4)}"
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.zadd(redis_key, {member: now})
        pipe.expire(redis_key, int(window_seconds) + 1)
        await pipe.execute()

    return False
