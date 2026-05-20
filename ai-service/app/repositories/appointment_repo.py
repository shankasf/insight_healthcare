import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentSlot


async def create_appointment(
    session: AsyncSession,
    *,
    slot_id: uuid.UUID,
    patient_name: str,
    patient_email: str,
    patient_phone: str | None,
    reason: str | None,
) -> Appointment:
    appt = Appointment(
        slot_id=slot_id,
        patient_name=patient_name,
        patient_email=patient_email,
        patient_phone=patient_phone,
        reason=reason,
        status="scheduled",
    )
    session.add(appt)
    await session.flush()
    await session.refresh(appt)
    return appt


async def get_by_id(session: AsyncSession, appointment_id: uuid.UUID) -> Appointment | None:
    return await session.get(Appointment, appointment_id)


async def get_with_slot(
    session: AsyncSession, appointment_id: uuid.UUID
) -> tuple[Appointment, AppointmentSlot] | None:
    stmt = (
        select(Appointment, AppointmentSlot)
        .join(AppointmentSlot, AppointmentSlot.id == Appointment.slot_id)
        .where(Appointment.id == appointment_id)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    return row[0], row[1]


async def cancel(
    session: AsyncSession,
    appointment_id: uuid.UUID,
    reason: str | None = None,
) -> Appointment | None:
    appt = await session.get(Appointment, appointment_id)
    if appt is None:
        return None
    appt.status = "cancelled"
    appt.cancellation_reason = reason
    await session.flush()
    return appt
