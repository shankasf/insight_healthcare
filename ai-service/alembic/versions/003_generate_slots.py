"""generate appointment_slots for next 14 weekdays + 3 sample bookings

Revision ID: 003_generate_slots
Revises: 002_seed_static
Create Date: 2026-05-20

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from scripts.seed_data import (
    SAMPLE_APPOINTMENTS,
    appointment_slot_target,
    generate_slots,
)

revision = "003_generate_slots"
down_revision = "002_seed_static"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    slots = generate_slots()
    if slots:
        bind.execute(
            sa.text(
                """
                INSERT INTO appointment_slots (provider_id, start_at, end_at, status)
                VALUES (:provider_id, :start_at, :end_at, :status)
                """
            ),
            [
                {
                    "provider_id": s.provider_id,
                    "start_at": s.start_at,
                    "end_at": s.end_at,
                    "status": s.status,
                }
                for s in slots
            ],
        )

    for appt in SAMPLE_APPOINTMENTS:
        target_start = appointment_slot_target(appt)
        slot_row = bind.execute(
            sa.text(
                """
                SELECT id FROM appointment_slots
                WHERE provider_id = :pid AND start_at = :start AND status = 'available'
                LIMIT 1
                """
            ),
            {"pid": appt.provider_id, "start": target_start},
        ).first()
        if slot_row is None:
            # If migration runs late in the day past the target slot, skip silently.
            continue
        slot_id = slot_row[0]

        bind.execute(
            sa.text(
                """
                INSERT INTO appointments (
                    slot_id, patient_name, patient_email, patient_phone, reason, status
                ) VALUES (
                    :slot_id, :patient_name, :patient_email, :patient_phone, :reason, 'scheduled'
                )
                """
            ),
            {
                "slot_id": slot_id,
                "patient_name": appt.patient_name,
                "patient_email": appt.patient_email,
                "patient_phone": appt.patient_phone,
                "reason": appt.reason,
            },
        )
        bind.execute(
            sa.text("UPDATE appointment_slots SET status = 'booked' WHERE id = :id"),
            {"id": slot_id},
        )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM appointments;"))
    bind.execute(sa.text("DELETE FROM appointment_slots;"))
