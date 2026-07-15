from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services import jwt_service, session_store
from app.services.admin_store import (
    AdminAlreadyExistsError,
    AdminAuthError,
    authenticate_admin,
    create_admin_account,
)
from app.services.turnstile import verify_turnstile

router = APIRouter()


class AdminLoginRequest(BaseModel):
    id: str
    pw: str
    captcha: str


class AdminSignupRequest(BaseModel):
    id: str
    pw: str
    secret: str


@router.post("/administrator-login")
async def administrator_login(payload: AdminLoginRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    if not await verify_turnstile(payload.captcha):
        raise HTTPException(status_code=401, detail="캡차 검증에 실패했습니다.")

    try:
        account = await authenticate_admin(db, login_id=payload.id, password=payload.pw)
    except AdminAuthError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

    token = jwt_service.create_access_token(account.user_id, "admin", account.login_id, role="admin")
    session_store.set_active_token(token)

    return {"status": "SUCCESS", "token": token}


@router.post("/administrator-signup")
async def administrator_signup(payload: AdminSignupRequest, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    if not settings.admin_signup_secret or payload.secret != settings.admin_signup_secret:
        raise HTTPException(status_code=403, detail="가입 시크릿키가 올바르지 않습니다.")

    try:
        account = await create_admin_account(db, login_id=payload.id, password=payload.pw)
    except AdminAlreadyExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    return {"status": "SUCCESS", "id": account.login_id}
