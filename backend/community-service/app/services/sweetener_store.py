import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag

_SWEETENER = "SWEETENER"


async def list_sweeteners(db: AsyncSession) -> list[Tag]:
    stmt = select(Tag).where(Tag.tag_type == _SWEETENER, Tag.active.is_(True)).order_by(Tag.tag_name)
    return list((await db.execute(stmt)).scalars().all())


async def get_sweetener(db: AsyncSession, tag_id: uuid.UUID) -> Tag | None:
    tag = await db.get(Tag, tag_id)
    if tag is None or tag.tag_type != _SWEETENER:
        return None
    return tag
