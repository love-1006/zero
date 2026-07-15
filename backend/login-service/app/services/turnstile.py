import httpx

from app.core.config import settings

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            VERIFY_URL,
            data={"secret": settings.turnstile_secret_key, "response": token},
        )
        response.raise_for_status()
        payload = response.json()

    return bool(payload.get("success"))
