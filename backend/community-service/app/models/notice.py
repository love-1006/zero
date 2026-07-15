import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Notice(Base):
    __tablename__ = "notices"
    __table_args__ = {"schema": "community"}

    notice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    # CM-0102 "뉴스 링크로 이동" — 외부 URL로 리다이렉트하는 공지도 있어서 본문과
    # 별개로 둔다 (community-service.md 설계 메모 참고).
    external_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # RESTRICT: 공지 작성 이력이 있는 관리자 계정은 실수로 삭제되지 않도록.
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
