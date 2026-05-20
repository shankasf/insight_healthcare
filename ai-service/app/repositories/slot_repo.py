import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import AppointmentSlot
from app.models.provider import Provider


@dataclass(slots=True)
class AvailableSlotView:
    slot_id: str
    provider_id: str
    provider_name: str
    start_at: datetime
    end_at: datetime


async def list_available_slots(
    session: AsyncSession,
    *,
    provider_id: uuid.UUID | None = None,
    from_date: datetime | None = None,
    days_ahead: int = 14,
    limit: int = 50,
) -> list[AvailableSlotView]:
    start = from_date or datetime.now(tz=timezone.utc)
    end = start + timedelta(days=days_ahead)

    conditions = [
        AppointmentSlot.status == "available",
        AppointmentSlot.start_at >= start,
        AppointmentSlot.start_at <= end,
    ]
    if provider_id is not None:
        conditions.append(AppointmentSlot.provider_id == provider_id)

    stmt = (
        select(
            AppointmentSlot.id,
            AppointmentSlot.provider_id,
            Provider.name,
            AppointmentSlot.start_at,
            AppointmentSlot.end_at,
        )
        .join(Provider, Provider.id == AppointmentSlot.provider_id)
        .where(and_(*conditions))
        .order_by(AppointmentSlot.start_at.asc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        AvailableSlotView(
            slot_id=str(r.id),
            provider_id=str(r.provider_id),
            provider_name=r.name,
            start_at=r.start_at,
            end_at=r.end_at,
        )
        for r in rows
    ]


async def get_slot(session: AsyncSession, slot_id: uuid.UUID) -> AppointmentSlot | None:
    return await session.get(AppointmentSlot, slot_id)


async def mark_slot_status(
    session: AsyncSession, slot_id: uuid.UUID, status: str
) -> AppointmentSlot | None:
    slot = await session.get(AppointmentSlot, slot_id)
    if slot is None:
        return None
    slot.status = status
    await session.flush()
    return slot


async def find_provider_by_name(session: AsyncSession, name: str) -> Provider | None:
    stmt = select(Provider).where(Provider.name.ilike(f"%{name}%"), Provider.active.is_(True))
    return (await session.execute(stmt)).scalars().first()
