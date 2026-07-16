from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal_log import MealLog
from app.models.meal_total import MealTotal

# "오늘"은 서버가 도는 지역과 무관하게 한국 사용자 기준 하루 — UTC 자정이 아니라
# KST 자정을 하루 경계로 쓴다.
_KST = ZoneInfo("Asia/Seoul")


async def get_today_totals(db: AsyncSession, user_id: int) -> tuple[float, float]:
    """(total_calories, total_sugars) consumed today (KST calendar day)."""
    now_kst = datetime.now(_KST)
    day_start = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = now_kst.replace(hour=23, minute=59, second=59, microsecond=999999)

    stmt = (
        select(
            func.coalesce(func.sum(MealTotal.total_calories), 0),
            func.coalesce(func.sum(MealTotal.total_sugars), 0),
        )
        .select_from(MealTotal)
        .join(MealLog, MealLog.meal_log_id == MealTotal.meal_log_id)
        .where(MealLog.user_id == user_id, MealLog.eaten_at >= day_start, MealLog.eaten_at <= day_end)
    )
    calories, sugars = (await db.execute(stmt)).one()
    return float(calories), float(sugars)
