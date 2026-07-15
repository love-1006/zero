import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag

_VALID_TAG_TYPES = {"CATEGORY", "ALLERGEN", "SWEETENER", "HEALTH_LABEL"}


class TagNotFoundError(Exception):
    pass


class DuplicateTagCodeError(Exception):
    pass


async def list_tags_by_type(db: AsyncSession, tag_type: str, active_only: bool = True) -> list[Tag]:
    stmt = select(Tag).where(Tag.tag_type == tag_type)
    if active_only:
        stmt = stmt.where(Tag.active.is_(True))
    stmt = stmt.order_by(Tag.tag_name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_tag(db: AsyncSession, tag_id: uuid.UUID) -> Tag:
    result = await db.execute(select(Tag).where(Tag.tag_id == tag_id))
    tag = result.scalar_one_or_none()
    if tag is None:
        raise TagNotFoundError(f"태그를 찾을 수 없습니다: {tag_id}")
    return tag


async def get_tag_with_product_count(db: AsyncSession, tag_id: uuid.UUID) -> dict:
    """관리자용 태그 상세 + 연결된 상품 수."""
    from sqlalchemy import text

    tag = await get_tag(db, tag_id)
    count_result = await db.execute(
        text("SELECT count(*) FROM service.product_tags WHERE tag_id = :tid"),
        {"tid": str(tag_id)},
    )
    product_count = count_result.scalar_one()
    return {
        "tag_id": str(tag.tag_id),
        "tag_type": tag.tag_type,
        "tag_code": tag.tag_code,
        "tag_name": tag.tag_name,
        "description": tag.description,
        "caution_text": tag.caution_text,
        "source_url": tag.source_url,
        "active": tag.active,
        "product_count": product_count,
    }


async def create_tag(
    db: AsyncSession,
    *,
    tag_type: str,
    tag_code: str,
    tag_name: str,
    description: str | None = None,
    caution_text: str | None = None,
    source_url: str | None = None,
) -> Tag:
    if tag_type not in _VALID_TAG_TYPES:
        raise ValueError(f"유효하지 않은 tag_type: {tag_type!r}. 허용 값: {_VALID_TAG_TYPES}")

    # UNIQUE (tag_type, tag_code) 중복 확인
    existing = await db.execute(
        select(Tag).where(Tag.tag_type == tag_type, Tag.tag_code == tag_code)
    )
    if existing.scalar_one_or_none() is not None:
        raise DuplicateTagCodeError(f"이미 존재하는 코드입니다: tag_type={tag_type!r}, tag_code={tag_code!r}")

    tag = Tag(
        tag_id=uuid.uuid4(),
        tag_type=tag_type,
        tag_code=tag_code,
        tag_name=tag_name,
        description=description,
        caution_text=caution_text,
        source_url=source_url,
        active=True,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def update_tag(
    db: AsyncSession,
    tag_id: uuid.UUID,
    *,
    tag_name: str | None = None,
    description: str | None = None,
    caution_text: str | None = None,
    source_url: str | None = None,
    active: bool | None = None,
) -> Tag:
    tag = await get_tag(db, tag_id)
    if tag_name is not None:
        tag.tag_name = tag_name
    if description is not None:
        tag.description = description
    if caution_text is not None:
        tag.caution_text = caution_text
    if source_url is not None:
        tag.source_url = source_url
    if active is not None:
        tag.active = active
    await db.commit()
    await db.refresh(tag)
    return tag
