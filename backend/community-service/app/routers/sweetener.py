import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.sweetener_store import get_sweetener, list_sweeteners

router = APIRouter(prefix="/community/gam-list")


@router.get("")
async def get_sweetener_list(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    tags = await list_sweeteners(db)
    return {"listGam": [{"id": str(tag.tag_id), "list": [{"name": tag.tag_name}]} for tag in tags]}


@router.get("/{tag_id}")
async def get_sweetener_detail(tag_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    tag = await get_sweetener(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="감미료 정보를 찾을 수 없습니다.")

    return {"listGam": [{"id": str(tag.tag_id), "list": [{"name": tag.tag_name, "desc": tag.description}]}]}
