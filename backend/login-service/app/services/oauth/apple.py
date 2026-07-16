from urllib.parse import urlencode

from app.core.config import settings
from app.services.oauth.types import NormalizedProfile, OAuthExchangeError

AUTHORIZE_URL = "https://appleid.apple.com/auth/authorize"


def build_authorize_url(state: str) -> str:
    # No `scope` requested on purpose: Apple only returns name/email once
    # (first authorization) and forces response_mode=form_post whenever any
    # scope is requested, which needs a POST callback route — this app's
    # /social-access/{provider}/callback is GET-only. Wire up scope + a POST
    # callback variant together with the real Apple Developer credentials
    # below, and verify against Apple's current docs before relying on this.
    params = {
        "response_type": "code",
        "response_mode": "query",
        "client_id": settings.apple_client_id,
        "redirect_uri": settings.apple_redirect_uri,
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str, state: str) -> str:
    # Apple authenticates the token request with a JWT "client_secret" signed
    # (ES256) using a Team ID / Key ID / private key (.p8) from the Apple
    # Developer portal — none of that exists yet, so this can't be implemented
    # correctly without guessing at credentials we don't have.
    raise OAuthExchangeError("Apple 로그인은 아직 구현되지 않았습니다 (Apple Developer 자격증명 필요).")


async def fetch_profile(access_token: str) -> NormalizedProfile:
    raise OAuthExchangeError("Apple 로그인은 아직 구현되지 않았습니다 (Apple Developer 자격증명 필요).")
