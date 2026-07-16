import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.models.user_preference import UserPreference

_TAG_BASED_TYPES = {"INTEREST_CATEGORY", "ALLERGEN"}


class InvalidPreferenceError(Exception):
    pass


class TagNotFoundError(Exception):
    pass


class DuplicatePreferenceError(Exception):
    pass


async def list_preferences(db: AsyncSession, user_id: int) -> list[UserPreference]:
    stmt = select(UserPreference).where(UserPreference.user_id == user_id)
    return list((await db.execute(stmt)).scalars().all())


async def add_preference(
    db: AsyncSession,
    user_id: int,
    preference_type: str,
    tag_id: uuid.UUID | None,
    custom_value: str | None,
) -> UserPreference:
    # DB CHECK constraints (ck_preferences_type/_type_value/_value) require
    # exactly this shape per type — validated here first for a clean 4xx
    # instead of a raw IntegrityError.
    if preference_type in _TAG_BASED_TYPES:
        if tag_id is None or custom_value is not None:
            raise InvalidPreferenceError(f"{preference_type}는 tag_id만 지정해야 합니다.")
        tag = await db.get(Tag, tag_id)
        if tag is None or not tag.active:
            raise TagNotFoundError("존재하지 않거나 비활성화된 태그입니다.")
    elif preference_type == "CAUTION_INGREDIENT":
        if custom_value is None or tag_id is not None:
            raise InvalidPreferenceError("CAUTION_INGREDIENT는 custom_value만 지정해야 합니다.")
    else:
        raise InvalidPreferenceError(f"알 수 없는 preference_type입니다: {preference_type!r}")

    preference = UserPreference(
        preference_id=uuid.uuid4(),
        user_id=user_id,
        preference_type=preference_type,
        tag_id=tag_id,
        custom_value=custom_value,
    )
    db.add(preference)
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise DuplicatePreferenceError("이미 등록된 선호 정보입니다.") from error

    await db.refresh(preference)
    return preference


async def remove_preference(db: AsyncSession, user_id: int, preference_id: uuid.UUID) -> bool:
    preference = await db.get(UserPreference, preference_id)
    if preference is None or preference.user_id != user_id:
        return False
    await db.delete(preference)
    await db.commit()
    return True
