from datetime import datetime

from sqlalchemy import ARRAY, CheckConstraint, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ClinicSettings(Base):
    __tablename__ = "clinic_settings"
    __table_args__ = (CheckConstraint("id = 1", name="ck_clinic_settings_singleton"),)

    # Singleton row enforced by CHECK (id = 1) — keeps single-tenant config without inventing a clinics table.
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address_line1: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    postal_code: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, default="America/Chicago")
    hours_json: Mapped[dict | None] = mapped_column(JSONB)
    services_offered: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
