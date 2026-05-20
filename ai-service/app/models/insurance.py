import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InsurancePlan(Base):
    __tablename__ = "insurance_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    payer_name: Mapped[str] = mapped_column(Text, nullable=False)
    plan_name: Mapped[str | None] = mapped_column(Text)
    accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )


class InsuranceMemberSample(Base):
    __tablename__ = "insurance_member_samples"
    __table_args__ = (UniqueConstraint("member_id", name="uq_insurance_member_samples_member_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("insurance_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    member_id: Mapped[str] = mapped_column(Text, nullable=False)
    member_name: Mapped[str] = mapped_column(Text, nullable=False)
    coverage_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    copay_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
