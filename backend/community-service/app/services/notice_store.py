import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notice import Notice
from app.models.notice_like import NoticeLike


class NoticeNotFoundError(Exception):
    pass


async def list_notices(db: AsyncSession) -> list[Notice]:
    stmt = select(Notice).order_by(Notice.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


async def get_notice(db: AsyncSession, notice_id: uuid.UUID) -> Notice:
    notice = await db.get(Notice, notice_id)
    if notice is None:
        raise NoticeNotFoundError("게시글을 찾을 수 없습니다.")
    return notice


async def count_likes(db: AsyncSession, notice_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(NoticeLike).where(NoticeLike.notice_id == notice_id)
    return (await db.execute(stmt)).scalar_one()


async def create_notice(
    db: AsyncSession,
    author_user_id: int,
    title: str,
    content: str,
    external_url: str | None,
    thumbnail_url: str | None,
    hashtag: str | None,
) -> Notice:
    notice = Notice(
        notice_id=uuid.uuid4(),
        title=title,
        content=content,
        external_url=external_url,
        thumbnail_url=thumbnail_url,
        hashtag=hashtag,
        author_user_id=author_user_id,
    )
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return notice


async def update_notice(
    db: AsyncSession,
    notice_id: uuid.UUID,
    *,
    title: str | None = None,
    content: str | None = None,
    external_url: str | None = None,
    thumbnail_url: str | None = None,
    hashtag: str | None = None,
) -> Notice:
    notice = await get_notice(db, notice_id)
    if title is not None:
        notice.title = title
    if content is not None:
        notice.content = content
    if external_url is not None:
        notice.external_url = external_url
    if thumbnail_url is not None:
        notice.thumbnail_url = thumbnail_url
    if hashtag is not None:
        notice.hashtag = hashtag
    notice.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(notice)
    return notice


async def delete_notice(db: AsyncSession, notice_id: uuid.UUID) -> None:
    notice = await get_notice(db, notice_id)
    await db.delete(notice)
    await db.commit()


async def toggle_like(db: AsyncSession, notice_id: uuid.UUID, user_id: int) -> tuple[bool, int]:
    await get_notice(db, notice_id)  # 404s if the notice doesn't exist

    existing = await db.get(NoticeLike, {"notice_id": notice_id, "user_id": user_id})
    if existing is not None:
        await db.delete(existing)
        await db.commit()
        liked = False
    else:
        db.add(NoticeLike(notice_id=notice_id, user_id=user_id))
        await db.commit()
        liked = True

    return liked, await count_likes(db, notice_id)
