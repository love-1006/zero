import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.diet_store import get_today_totals, get_user_health_profile

logger = logging.getLogger("diet_service.home")

router = APIRouter(prefix="/home")


@router.get("/user-sugar-calorie")
async def user_sugar_calorie(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user),
) -> dict[str, object]:
    """MN-0106~0108: 오늘 하루 당/칼로리 섭취량 + 목표 대비 비율.

    - MN-0106: 기본 섭취 수치
    - MN-0107: 칼로리 신호등용 수치
    - MN-0108: 당 각설탕 환산용 수치
    같은 엔드포인트로 세 기능 모두 처리 (프론트가 표현 방식만 다름).
    """
    user_id: int = payload["user_id"]

    totals = await get_today_totals(db, user_id)
    profile = await get_user_health_profile(db, user_id)

    cal_target = float(profile.daily_calorie_target) if profile and profile.daily_calorie_target else None
    sugar_target = float(profile.daily_sugar_target_g) if profile and profile.daily_sugar_target_g else None

    logger.info("home: sugar-calorie query user_id=%s", user_id)
    return {
        "cal": totals["cal"],
        "sugar": totals["sugar"],
        "cal_target": cal_target,
        "sugar_target": sugar_target,
    }
