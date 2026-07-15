import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services import jwt_service, rate_limiter, session_store
from app.services.admin_store import (
    AdminAlreadyExistsError,
    AdminAuthError,
    authenticate_admin,
    create_admin_account,
)
from app.services.turnstile import verify_turnstile

logger = logging.getLogger("app.admin_auth")

router = APIRouter()

# SC-0104: anti-automation on admin auth endpoints. Two keys on login — per IP
# (credential stuffing across accounts) and per login id (brute force on one
# account regardless of source IP) — since either alone misses one attack shape.
_LOGIN_MAX_ATTEMPTS_PER_IP = 20
_LOGIN_MAX_ATTEMPTS_PER_ID = 5
_SIGNUP_MAX_ATTEMPTS_PER_IP = 10


class AdminLoginRequest(BaseModel):
    id: str
    pw: str
    captcha: str


class AdminSignupRequest(BaseModel):
    id: str
    pw: str
    secret: str


@router.post("/administrator-login")
async def administrator_login(
    payload: AdminLoginRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    ip_blocked = rate_limiter.hit(f"admin-login:ip:{client_ip}", _LOGIN_MAX_ATTEMPTS_PER_IP)
    id_blocked = rate_limiter.hit(f"admin-login:id:{payload.id}", _LOGIN_MAX_ATTEMPTS_PER_ID)
    if ip_blocked or id_blocked:
        logger.warning("admin login denied: reason=rate_limited login_id=%r ip=%s", payload.id, client_ip)
        raise HTTPException(status_code=429, detail="너무 많은 시도가 있었습니다. 잠시 후 다시 시도해주세요.")

    # %r (not %s) on user-supplied fields — escapes newlines/control chars so a
    # crafted login id can't forge extra log lines (log injection, ASVS V16.4.1).
    if not await verify_turnstile(payload.captcha):
        logger.warning("admin login denied: reason=captcha_failed login_id=%r", payload.id)
        raise HTTPException(status_code=401, detail="캡차 검증에 실패했습니다.")

    try:
        account = await authenticate_admin(db, login_id=payload.id, password=payload.pw)
    except AdminAuthError as error:
        logger.warning("admin login denied: reason=invalid_credentials login_id=%r", payload.id)
        raise HTTPException(status_code=401, detail=str(error)) from error

    token = jwt_service.create_access_token(account.user_id, "admin", account.login_id, role="admin")
    session_store.set_active_token(token)
    logger.info("admin login success: user_id=%s login_id=%r", account.user_id, account.login_id)

    return {"status": "SUCCESS", "token": token}


@router.post("/administrator-signup")
async def administrator_signup(
    payload: AdminSignupRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    if rate_limiter.hit(f"admin-signup:ip:{client_ip}", _SIGNUP_MAX_ATTEMPTS_PER_IP):
        logger.warning("admin signup denied: reason=rate_limited ip=%s", client_ip)
        raise HTTPException(status_code=429, detail="너무 많은 시도가 있었습니다. 잠시 후 다시 시도해주세요.")

    if not settings.admin_signup_secret or payload.secret != settings.admin_signup_secret:
        logger.warning("admin signup denied: reason=invalid_secret login_id=%r", payload.id)
        raise HTTPException(status_code=403, detail="가입 시크릿키가 올바르지 않습니다.")

    try:
        account = await create_admin_account(db, login_id=payload.id, password=payload.pw)
    except AdminAlreadyExistsError as error:
        logger.warning("admin signup denied: reason=already_exists login_id=%r", payload.id)
        raise HTTPException(status_code=409, detail=str(error)) from error

    logger.info("admin signup success: user_id=%s login_id=%r", account.user_id, account.login_id)
    return {"status": "SUCCESS", "id": account.login_id}
