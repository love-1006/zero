import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal_item import MealItem
from app.models.meal_log import MealLog
from app.models.product_ref import ProductRef
from app.models.user_health_profile_ref import UserHealthProfileRef


class MealLogNotFoundError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


# ── MealLog ──────────────────────────────────────────────────────────────────

async def create_meal_log(
    db: AsyncSession,
    *,
    user_id: int,
    image_url: str,
    meal_type: str = "SNACK",
    input_type: str = "VISION",
) -> MealLog:
    log = MealLog(
        meal_log_id=uuid.uuid4(),
        user_id=user_id,
        input_type=input_type,
        meal_type=meal_type,
        image_url=image_url,
        analysis_status="PENDING",
        eaten_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def get_meal_log(db: AsyncSession, meal_log_id: uuid.UUID) -> MealLog:
    result = await db.execute(select(MealLog).where(MealLog.meal_log_id == meal_log_id))
    log = result.scalar_one_or_none()
    if log is None:
        raise MealLogNotFoundError(f"식단 기록을 찾을 수 없습니다: {meal_log_id}")
    return log


async def get_meal_log_for_user(db: AsyncSession, meal_log_id: uuid.UUID, user_id: int) -> MealLog:
    """소유자 검증 포함 조회."""
    log = await get_meal_log(db, meal_log_id)
    if log.user_id != user_id:
        raise MealLogNotFoundError(f"식단 기록을 찾을 수 없습니다: {meal_log_id}")
    return log


async def complete_meal_log(db: AsyncSession, meal_log_id: uuid.UUID, items: list[MealItem]) -> MealLog:
    """AI 분석 완료 처리: meal_items insert + status=COMPLETED."""
    log = await get_meal_log(db, meal_log_id)
    for item in items:
        db.add(item)
    log.analysis_status = "COMPLETED"
    await db.commit()
    await db.refresh(log)
    return log


async def list_meal_logs_by_month(
    db: AsyncSession,
    user_id: int,
    year: int,
    month: int,
) -> list[MealLog]:
    """RC-0106: 월별 캘린더용 식단 목록."""
    from datetime import date
    import calendar

    _, last_day = calendar.monthrange(year, month)
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    result = await db.execute(
        select(MealLog)
        .where(MealLog.user_id == user_id)
        .where(MealLog.eaten_at >= start)
        .where(MealLog.eaten_at <= end)
        .order_by(MealLog.eaten_at)
    )
    return list(result.scalars().all())


# ── MealItem ─────────────────────────────────────────────────────────────────

async def get_meal_items(db: AsyncSession, meal_log_id: uuid.UUID) -> list[MealItem]:
    result = await db.execute(
        select(MealItem).where(MealItem.meal_log_id == meal_log_id)
    )
    return list(result.scalars().all())


def make_meal_item_from_product(meal_log_id: uuid.UUID, product: ProductRef) -> MealItem:
    """Product 현재 값을 스냅샷으로 복제해 MealItem 생성."""
    return MealItem(
        meal_item_id=uuid.uuid4(),
        meal_log_id=meal_log_id,
        product_id=product.product_id,
        item_name=product.product_name,
        calories=product.calories,
        sugars=product.sugars,
        carbohydrate=product.carbohydrate,
        protein=product.protein,
        fat=product.fat,
        sodium=product.sodium,
    )


def make_meal_item_from_analysis(
    meal_log_id: uuid.UUID,
    item_name: str,
    calories: Decimal | None = None,
    sugars: Decimal | None = None,
    carbohydrate: Decimal | None = None,
    protein: Decimal | None = None,
    fat: Decimal | None = None,
    sodium: Decimal | None = None,
    raw_analysis: str | None = None,
) -> MealItem:
    """AI/OCR 분석 결과로 MealItem 생성 (product_id 없음)."""
    return MealItem(
        meal_item_id=uuid.uuid4(),
        meal_log_id=meal_log_id,
        item_name=item_name,
        calories=calories,
        sugars=sugars,
        carbohydrate=carbohydrate,
        protein=protein,
        fat=fat,
        sodium=sodium,
        raw_analysis=raw_analysis,
    )


# ── Product 스냅샷 조회 ───────────────────────────────────────────────────────

async def get_product_ref(db: AsyncSession, product_id: uuid.UUID) -> ProductRef:
    result = await db.execute(select(ProductRef).where(ProductRef.product_id == product_id))
    p = result.scalar_one_or_none()
    if p is None:
        raise ProductNotFoundError(f"상품을 찾을 수 없습니다: {product_id}")
    return p


# ── 홈 당/칼로리 게이지 (MN-0106~0108) ────────────────────────────────────────

async def get_today_totals(db: AsyncSession, user_id: int) -> dict:
    """오늘 날짜 칼로리/당 합계 — v_meal_totals 뷰 기반."""
    row = await db.execute(
        text("""
            SELECT
                COALESCE(SUM(vt.total_calories), 0) AS calories,
                COALESCE(SUM(vt.total_sugars), 0)   AS sugars
            FROM service.meal_logs ml
            JOIN service.v_meal_totals vt ON vt.meal_log_id = ml.meal_log_id
            WHERE ml.user_id = :uid
              AND date_trunc('day', ml.eaten_at AT TIME ZONE 'UTC') =
                  date_trunc('day', now() AT TIME ZONE 'UTC')
        """),
        {"uid": user_id},
    )
    r = row.one()
    return {"cal": float(r.calories), "sugar": float(r.sugars)}


# ── 사용자 건강 프로필 (MN-0106 게이지 목표값) ──────────────────────────────────

async def get_user_health_profile(
    db: AsyncSession, user_id: int
) -> UserHealthProfileRef | None:
    result = await db.execute(
        select(UserHealthProfileRef).where(UserHealthProfileRef.user_id == user_id)
    )
    return result.scalar_one_or_none()
