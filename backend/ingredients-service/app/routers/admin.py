import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin
from app.core.database import get_db
from app.services.tag_store import (
    DuplicateTagCodeError,
    TagNotFoundError,
    create_tag,
    update_tag,
)

logger = logging.getLogger("ingredients_service.admin")

router = APIRouter(prefix="/admin")

_VALID_TAG_TYPES = {"CATEGORY", "ALLERGEN", "SWEETENER", "HEALTH_LABEL"}


def _parse_uuid(value: str, label: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"유효하지 않은 {label} UUID 형식입니다.")


@router.post("")
async def admin_endpoint(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
) -> dict[str, object]:
    """AD-0104 (태그 마스터 관리): menu=create-tag | update-tag | deactivate-tag."""
    menu = body.get("menu", "")

    if menu == "create-tag":
        return await _handle_create_tag(body, db)

    if menu == "update-tag":
        return await _handle_update_tag(body, db)

    if menu == "deactivate-tag":
        return await _handle_deactivate_tag(body, db)

    raise HTTPException(status_code=422, detail=f"알 수 없는 menu 값입니다: {menu!r}")


async def _handle_create_tag(body: dict, db: AsyncSession) -> dict[str, object]:
    """새 태그 신설 (알레르기 유형 추가 / 감미료 유형 추가 등)."""
    for field in ("tag_type", "tag_code", "tag_name"):
        if not body.get(field):
            raise HTTPException(status_code=422, detail=f"필수 필드 누락: {field}")

    tag_type = body["tag_type"].upper()
    if tag_type not in _VALID_TAG_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"유효하지 않은 tag_type: {tag_type!r}. 허용 값: {sorted(_VALID_TAG_TYPES)}",
        )

    try:
        tag = await create_tag(
            db,
            tag_type=tag_type,
            tag_code=body["tag_code"],
            tag_name=body["tag_name"],
            description=body.get("description"),
            caution_text=body.get("caution_text"),
            source_url=body.get("source_url"),
        )
    except DuplicateTagCodeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    logger.info("admin: tag created tag_id=%s tag_type=%s", tag.tag_id, tag.tag_type)
    return {"status": "SUCCESS", "id": str(tag.tag_id)}


async def _handle_update_tag(body: dict, db: AsyncSession) -> dict[str, object]:
    """태그 설명/이름 수정."""
    if not body.get("id"):
        raise HTTPException(status_code=422, detail="필수 필드 누락: id")
    tid = _parse_uuid(body["id"], "태그 ID")

    try:
        await update_tag(
            db,
            tid,
            tag_name=body.get("tag_name"),
            description=body.get("description"),
            caution_text=body.get("caution_text"),
            source_url=body.get("source_url"),
        )
    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    logger.info("admin: tag updated tag_id=%s", tid)
    return {"status": "SUCCESS", "id": str(tid)}


async def _handle_deactivate_tag(body: dict, db: AsyncSession) -> dict[str, object]:
    """태그 비활성화 (active=false). 삭제 불가 — RESTRICT 정책."""
    if not body.get("id"):
        raise HTTPException(status_code=422, detail="필수 필드 누락: id")
    tid = _parse_uuid(body["id"], "태그 ID")

    try:
        await update_tag(db, tid, active=False)
    except TagNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    logger.info("admin: tag deactivated tag_id=%s", tid)
    return {"status": "SUCCESS", "id": str(tid)}
