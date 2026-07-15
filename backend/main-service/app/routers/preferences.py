import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_from_token
from app.services.preference_store import (
    DuplicatePreferenceError,
    InvalidPreferenceError,
    TagNotFoundError,
    add_preference,
    list_preferences,
    remove_preference,
)

router = APIRouter(prefix="/home/preferences")


class AddPreferenceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    usr: str
    preference_type: Annotated[str, Field(alias="preferenceType")]
    tag_id: Annotated[uuid.UUID | None, Field(alias="tagId")] = None
    custom_value: Annotated[str | None, Field(alias="customValue")] = None


@router.get("")
async def get_preferences(usr: str, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    user = get_current_user_from_token(usr)
    preferences = await list_preferences(db, user.user_id)
    return {
        "preferences": [
            {
                "preferenceId": str(p.preference_id),
                "preferenceType": p.preference_type,
                "tagId": str(p.tag_id) if p.tag_id else None,
                "customValue": p.custom_value,
            }
            for p in preferences
        ]
    }


@router.post("")
async def create_preference(payload: AddPreferenceRequest, db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    user = get_current_user_from_token(payload.usr)
    try:
        preference = await add_preference(
            db, user.user_id, payload.preference_type, payload.tag_id, payload.custom_value
        )
    except InvalidPreferenceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except TagNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DuplicatePreferenceError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    return {"status": "SUCCESS", "preferenceId": str(preference.preference_id)}


@router.delete("/{preference_id}")
async def delete_preference(
    preference_id: uuid.UUID, usr: str, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    user = get_current_user_from_token(usr)
    deleted = await remove_preference(db, user.user_id, preference_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="선호 정보를 찾을 수 없습니다.")
    return {"status": "SUCCESS"}
