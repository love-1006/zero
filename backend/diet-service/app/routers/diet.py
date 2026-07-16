import json
import logging
import uuid
from decimal import Decimal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.services.diet_store import (
    MealLogNotFoundError,
    ProductNotFoundError,
    complete_meal_log,
    create_meal_log,
    get_meal_items,
    get_meal_log_for_user,
    get_product_ref,
    list_meal_logs_by_month,
    make_meal_item_from_analysis,
    make_meal_item_from_product,
)

logger = logging.getLogger("diet_service.diet")

router = APIRouter(prefix="/diet")


def _to_uuid(value: str, label: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"유효하지 않은 {label} UUID 형식입니다.")


def _item_dict(item) -> dict:
    # service.meal_items에는 단백질/지방/나트륨 컬럼이 없다(실제 스키마 확인
    # 완료) — 있는 것처럼 꾸미지 않고 null로 명시한다.
    return {
        "name": item.item_name,
        "dang": float(item.sugars) if item.sugars is not None else None,
        "calo": float(item.calories) if item.calories is not None else None,
        "ingred-list": [
            {"name": "탄수화물", "amount": float(item.carbohydrate) if item.carbohydrate is not None else None},
            {"name": "단백질", "amount": None},
            {"name": "지방", "amount": None},
            {"name": "나트륨", "amount": None},
        ],
    }


# RC-0101: 한끼 식단 사진 업로드
# RC-0102: 하루 식단 사진 업로드 (mode=daily)
@router.post("/upload")
async def upload_diet(
    body: dict,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user),
) -> dict[str, object]:
    """RC-0101~0102: 식단 사진 URL 등록 → meal_log 생성 (분석은 별도 호출).

    body: {img: S3_URL, mode: 'daily'(optional)}
    """
    user_id: int = payload["user_id"]
    image_object_key: str | None = body.get("img")
    if not image_object_key:
        raise HTTPException(status_code=422, detail="필수 필드 누락: img")

    # 실제 DB의 meal_type CHECK 제약엔 'DAILY'가 없다(BREAKFAST/LUNCH/DINNER/
    # SNACK/OTHER만 허용) — "하루 식단" 업로드는 OTHER로 매핑한다.
    meal_type = "OTHER" if body.get("mode") == "daily" else "SNACK"

    log = await create_meal_log(
        db,
        user_id=user_id,
        image_object_key=image_object_key,
        meal_type=meal_type,
        input_type="VISION",
    )
    logger.info("diet: meal_log created meal_log_id=%s user_id=%s", log.meal_log_id, user_id)
    return {"status": "SUCCESS", "id": str(log.meal_log_id)}


# RC-0103: AI 식단 분석 (Vision AI → 음식 인식 + 영양 추정)
@router.get("/ai-analyze")
async def ai_analyze(
    id: str = Query(..., description="meal_log UUID"),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user),
) -> dict[str, object]:
    """RC-0103: meal_log의 이미지를 AI로 분석해 meal_items 저장.

    실제 Vision AI 파이프라인 미구현 → PREPARING 상태 반환.
    구현 시: 이미지 URL로 Claude Vision 또는 외부 API 호출,
    응답 파싱 후 make_meal_item_from_analysis로 items 생성,
    complete_meal_log(db, id, items) 로 저장.
    """
    user_id: int = payload["user_id"]
    log_id = _to_uuid(id, "meal_log ID")

    try:
        await get_meal_log_for_user(db, log_id, user_id)
    except MealLogNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "status": "PREPARING",
        "message": "AI 식단 분석 기능은 Vision AI 파이프라인 연동 후 활성화됩니다.",
        "id": str(log_id),
        "list-diet": [],
    }


# RC-0104: OCR 분석 결과 (제품 영양성분 표 인식)
@router.get("/other-foods")
async def other_foods(
    id: str = Query(..., description="meal_log UUID"),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user),
) -> dict[str, object]:
    """RC-0104: meal_log에 저장된 분석 결과 조회 (합계 + 항목 목록).

    upload 후 ai-analyze 완료된 결과를 읽어 반환.
    """
    user_id: int = payload["user_id"]
    log_id = _to_uuid(id, "meal_log ID")

    try:
        log = await get_meal_log_for_user(db, log_id, user_id)
    except MealLogNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if log.analysis_status == "PENDING":
        return {"status": "PENDING", "message": "분석이 아직 완료되지 않았습니다.", "id": str(log_id)}

    items = await get_meal_items(db, log_id)
    total_cal = sum(float(i.calories or 0) for i in items)
    total_sugar = sum(float(i.sugars or 0) for i in items)

    return {
        "id": str(log_id),
        "dang": total_sugar,
        "calo": total_cal,
        "list-diet": [_item_dict(i) for i in items],
    }


# RC-0105: 대체 제품 추천 (Product Service 검색 API 위임)
@router.get("/recommend-alt")
async def recommend_alt(
    id: str = Query(..., description="meal_log UUID"),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user),
) -> dict[str, object]:
    """RC-0105: 식단 내 제품의 저당/제로 대체 제품 추천 (Product Service 검색 위임).

    현재 PREPARING — Product Service /search 연동 후 활성화.
    """
    user_id: int = payload["user_id"]
    log_id = _to_uuid(id, "meal_log ID")

    try:
        await get_meal_log_for_user(db, log_id, user_id)
    except MealLogNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "status": "PREPARING",
        "message": "대체 제품 추천 기능은 Product Service 연동 후 활성화됩니다.",
        "list-products": [],
    }


# RC-0106: 캘린더 (날짜별 식단 기록)
@router.get("/calender")
async def calender(
    year: int = Query(..., description="연도 (예: 2026)"),
    month: int = Query(..., ge=1, le=12, description="월 (1~12)"),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user),
) -> dict[str, object]:
    """RC-0106: 월별 캘린더 — 날짜별 식단 목록."""
    user_id: int = payload["user_id"]

    logs = await list_meal_logs_by_month(db, user_id, year, month)
    return {
        "list": [
            {
                "date": log.eaten_at.strftime("%Y-%m-%d"),
                "name": log.meal_type,
                # usr는 토큰이라 응답에 그대로 안 심는다 — 프론트가 자기 토큰으로 붙여서 호출.
                "url": f"/diet/other-foods?id={log.meal_log_id}",
            }
            for log in logs
        ]
    }
