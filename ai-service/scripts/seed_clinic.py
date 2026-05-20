"""Idempotent re-runner of migrations 002 + 003.

Useful for re-seeding after dev-DB resets or to refresh slot windows so the
demo always has fresh "tomorrow" slots.

Run with:  python -m scripts.seed_clinic
"""
from __future__ import annotations

import asyncio
import json

from sqlalchemy import text

from app.core.db import session_scope
from scripts.seed_data import (
    CLINIC_FAQS,
    CLINIC_SETTINGS,
    INSURANCE_MEMBER_SAMPLES,
    INSURANCE_PLANS,
    PROVIDERS,
    SAMPLE_APPOINTMENTS,
    appointment_slot_target,
    generate_slots,
)


async def _seed_clinic_settings(session) -> None:
    await session.execute(
        text(
            """
            INSERT INTO clinic_settings (
                id, name, address_line1, city, state, postal_code, phone, email,
                timezone, hours_json, services_offered
            ) VALUES (
                :id, :name, :address_line1, :city, :state, :postal_code, :phone, :email,
                :timezone, CAST(:hours_json AS JSONB), :services_offered
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                address_line1 = EXCLUDED.address_line1,
                city = EXCLUDED.city,
                state = EXCLUDED.state,
                postal_code = EXCLUDED.postal_code,
                phone = EXCLUDED.phone,
                email = EXCLUDED.email,
                timezone = EXCLUDED.timezone,
                hours_json = EXCLUDED.hours_json,
                services_offered = EXCLUDED.services_offered,
                updated_at = now();
            """
        ),
        {**CLINIC_SETTINGS, "hours_json": json.dumps(CLINIC_SETTINGS["hours_json"])},
    )


async def _seed_providers(session) -> None:
    for p in PROVIDERS:
        await session.execute(
            text(
                """
                INSERT INTO providers (id, name, role, email, phone, active)
                VALUES (:id, :name, :role, :email, :phone, :active)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    active = EXCLUDED.active,
                    updated_at = now();
                """
            ),
            p,
        )


async def _seed_insurance(session) -> None:
    for plan in INSURANCE_PLANS:
        await session.execute(
            text(
                """
                INSERT INTO insurance_plans (
                    id, payer_name, plan_name, accepted, notes, effective_from, effective_to
                ) VALUES (
                    :id, :payer_name, :plan_name, :accepted, :notes, :effective_from, :effective_to
                )
                ON CONFLICT (id) DO UPDATE SET
                    payer_name = EXCLUDED.payer_name,
                    plan_name = EXCLUDED.plan_name,
                    accepted = EXCLUDED.accepted,
                    notes = EXCLUDED.notes,
                    effective_from = EXCLUDED.effective_from,
                    effective_to = EXCLUDED.effective_to,
                    updated_at = now();
                """
            ),
            plan,
        )
    for m in INSURANCE_MEMBER_SAMPLES:
        await session.execute(
            text(
                """
                INSERT INTO insurance_member_samples (
                    id, plan_id, member_id, member_name, coverage_active, copay_amount,
                    effective_from, effective_to, notes
                ) VALUES (
                    :id, :plan_id, :member_id, :member_name, :coverage_active, :copay_amount,
                    :effective_from, :effective_to, :notes
                )
                ON CONFLICT (member_id) DO UPDATE SET
                    plan_id = EXCLUDED.plan_id,
                    member_name = EXCLUDED.member_name,
                    coverage_active = EXCLUDED.coverage_active,
                    copay_amount = EXCLUDED.copay_amount,
                    effective_from = EXCLUDED.effective_from,
                    effective_to = EXCLUDED.effective_to,
                    notes = EXCLUDED.notes;
                """
            ),
            m,
        )


async def _seed_faqs(session) -> None:
    for faq in CLINIC_FAQS:
        await session.execute(
            text(
                """
                INSERT INTO clinic_faqs (question, answer, tags, active)
                SELECT :question, :answer, :tags, true
                WHERE NOT EXISTS (
                    SELECT 1 FROM clinic_faqs WHERE question = :question
                );
                """
            ),
            {"question": faq["question"], "answer": faq["answer"], "tags": faq["tags"]},
        )


async def _seed_slots_and_appointments(session) -> None:
    # Wipe and regenerate so the demo always has fresh future slots.
    # Cancel/orphan appointments referencing slots we're about to delete.
    await session.execute(text("DELETE FROM appointments;"))
    await session.execute(text("DELETE FROM appointment_slots;"))

    slots = generate_slots()
    if slots:
        await session.execute(
            text(
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
        row = (
            await session.execute(
                text(
                    """
                    SELECT id FROM appointment_slots
                    WHERE provider_id = :pid AND start_at = :start AND status = 'available'
                    LIMIT 1
                    """
                ),
                {"pid": appt.provider_id, "start": target_start},
            )
        ).first()
        if row is None:
            continue
        slot_id = row[0]
        await session.execute(
            text(
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
        await session.execute(
            text("UPDATE appointment_slots SET status = 'booked' WHERE id = :id"),
            {"id": slot_id},
        )


async def main() -> None:
    async with session_scope() as session:
        await _seed_clinic_settings(session)
        await _seed_providers(session)
        await _seed_insurance(session)
        await _seed_faqs(session)
        await _seed_slots_and_appointments(session)
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
