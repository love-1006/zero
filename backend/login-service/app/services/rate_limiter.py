import time

# Temporary in-memory store until Redis is wired up; resets on every restart
# and only limits within a single process (won't hold once we run >1 instance).
_WINDOW_SECONDS = 60.0

_windows: dict[str, list[float]] = {}


def hit(key: str, max_attempts: int, window_seconds: float = _WINDOW_SECONDS) -> bool:
    """Record an attempt under `key` and report whether it should be blocked.

    Returns True (blocked) without recording the attempt if `key` already has
    `max_attempts` hits within the trailing `window_seconds`.
    """
    now = time.monotonic()
    timestamps = [t for t in _windows.get(key, []) if t > now - window_seconds]

    if len(timestamps) >= max_attempts:
        _windows[key] = timestamps
        return True

    timestamps.append(now)
    _windows[key] = timestamps
    return False
