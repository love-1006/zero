import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProductTag(Base):
    """Product Service 소유. (product_id, tag_id) 복합 PK.

    evidence_source: 실제 DB에 NOT NULL + CHECK IN ('NAME','NUTRITION',
    'INGREDIENT','CRAWL') 제약이 있음 — 이 태그 매칭이 어떤 근거로 만들어졌는지
    기록. 관리자가 수동으로 카테고리/알레르기 태그를 지정하는 현재 흐름에는
    정확히 맞는 값이 없지만, 이름 기반으로 매칭한다고 보고 'NAME'을 사용한다
    (product_store.py 참고).
    """

    __tablename__ = "product_tags"
    __table_args__ = {"schema": "service"}

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    evidence_source: Mapped[str] = mapped_column(String(30))
    matched_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
