from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRef(Base):
    """login-service owns the real `users` table (public schema) — this is a
    minimal stub so SQLAlchemy can resolve FKs from this service's own tables
    (notices.author_user_id, notice_likes.user_id) to it. Never written to,
    and never included in create_all() (see OWNED_TABLES below)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
