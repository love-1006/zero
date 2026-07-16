from app.models.notice import Notice
from app.models.notice_like import NoticeLike
from app.models.tag import Tag
from app.models.user_ref import UserRef

__all__ = ["Notice", "NoticeLike", "Tag", "UserRef"]

# Tables this service owns and self-migrates via create_all() in app/main.py.
# Tag (service.tags) and UserRef (public.users) are READ-ONLY — Ingredients
# Service and login-service own them respectively, and must never be included
# here, or create_all() would try to create/alter them too.
OWNED_TABLES = [Notice.__table__, NoticeLike.__table__]
