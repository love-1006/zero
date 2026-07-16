from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_health_profile import UserHealthProfile

_HEALTH_FIELDS = (
    "birth_year",
    "gender",
    "height_cm",
    "weight_kg",
    "activity_level",
    "health_goal",
    "daily_calorie_target",
    "daily_sugar_target_g",
)


class HealthDataConsentRequiredError(Exception):
    pass


async def get_health_profile(db: AsyncSession, user_id: int) -> UserHealthProfile | None:
    return await db.get(UserHealthProfile, user_id)


async def upsert_health_profile(
    db: AsyncSession,
    user_id: int,
    *,
    consent: bool,
    birth_year: int | None = None,
    gender: str | None = None,
    height_cm: float | None = None,
    weight_kg: float | None = None,
    activity_level: str | None = None,
    health_goal: str | None = None,
    daily_calorie_target: float | None = None,
    daily_sugar_target_g: float | None = None,
) -> UserHealthProfile:
    profile = await db.get(UserHealthProfile, user_id)
    if profile is None:
        profile = UserHealthProfile(user_id=user_id)
        db.add(profile)

    if birth_year is not None:
        profile.birth_year = birth_year
    if gender is not None:
        profile.gender = gender
    if height_cm is not None:
        profile.height_cm = Decimal(str(height_cm))
    if weight_kg is not None:
        profile.weight_kg = Decimal(str(weight_kg))
    if activity_level is not None:
        profile.activity_level = activity_level
    if health_goal is not None:
        profile.health_goal = health_goal
    if daily_calorie_target is not None:
        profile.daily_calorie_target = Decimal(str(daily_calorie_target))
        profile.target_source = "USER"
    if daily_sugar_target_g is not None:
        profile.daily_sugar_target_g = Decimal(str(daily_sugar_target_g))
        profile.target_source = "USER"

    # Mirrors the DB CHECK constraint (ck_health_consent): a consent timestamp
    # must be present the moment any health field is non-null, and absent
    # when none are. Enforced here too so callers get a clean 4xx instead of
    # a raw IntegrityError from the DB.
    has_any_health_field = any(getattr(profile, field) is not None for field in _HEALTH_FIELDS)
    if has_any_health_field:
        if not consent:
            raise HealthDataConsentRequiredError("건강정보를 저장하려면 수집 동의(consent)가 필요합니다.")
        if profile.health_data_consent_at is None:
            profile.health_data_consent_at = datetime.now(timezone.utc)
    else:
        profile.health_data_consent_at = None

    await db.commit()
    await db.refresh(profile)
    return profile
