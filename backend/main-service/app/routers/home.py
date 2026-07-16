from fastapi import APIRouter, Response

from app.core.security import get_current_user_from_token

router = APIRouter(prefix="/home")


@router.get("/me")
async def get_current_user_identity(usr: str, response: Response) -> dict[str, object]:
    user = get_current_user_from_token(usr, response)
    return {"userId": user.user_id, "nickname": user.nickname}
