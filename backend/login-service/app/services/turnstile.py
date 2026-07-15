import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("app.turnstile")

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: str) -> bool:
    # Cloudflare can answer with a non-200 (e.g. malformed/misconfigured secret)
    # instead of the usual 200 + {"success": false} — treat any failure to reach
    # a clean verdict as "not verified" rather than crashing the login request.
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                VERIFY_URL,
                data={"secret": settings.turnstile_secret_key, "response": token},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as error:
        logger.warning("turnstile verification failed: reason=request_error error=%r", str(error))
        return False

    if not payload.get("success"):
        logger.info("turnstile verification failed: reason=rejected error_codes=%r", payload.get("error-codes"))

    return bool(payload.get("success"))
