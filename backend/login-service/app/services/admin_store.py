from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin_account import AdminAccount
from app.models.user import User
from app.services.security import hash_password, verify_password


class AdminAuthError(Exception):
    pass


class AdminAlreadyExistsError(Exception):
    pass


async def create_admin_account(db: AsyncSession, login_id: str, password: str) -> AdminAccount:
    existing = await db.scalar(select(AdminAccount).where(AdminAccount.login_id == login_id))
    if existing is not None:
        raise AdminAlreadyExistsError(f"이미 존재하는 관리자 아이디입니다: {login_id}")

    user = User()
    account = AdminAccount(user=user, login_id=login_id, password_hash=hash_password(password))
    db.add(user)
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def authenticate_admin(db: AsyncSession, login_id: str, password: str) -> AdminAccount:
    stmt = (
        select(AdminAccount)
        .where(AdminAccount.login_id == login_id)
        .options(selectinload(AdminAccount.user))
    )
    account = (await db.execute(stmt)).scalar_one_or_none()

    if account is None or not verify_password(password, account.password_hash):
        raise AdminAuthError("아이디 또는 비밀번호가 올바르지 않습니다.")

    return account
