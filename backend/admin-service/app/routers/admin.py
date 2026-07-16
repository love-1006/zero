from fastapi import APIRouter, Depends

from app.core.security import AdminIdentity, get_current_admin

router = APIRouter(prefix="/admin")


@router.get("/me")
async def get_admin_identity(admin: AdminIdentity = Depends(get_current_admin)) -> dict[str, object]:
    return {"userId": admin.user_id, "loginId": admin.login_id}
