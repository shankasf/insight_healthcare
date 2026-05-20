import uuid
from datetime import datetime

from agents import function_tool

from app.core.db import session_scope
from app.repositories import (
    appointment_repo,
    clinic_repo,
    faq_repo,
    insurance_repo,
    slot_repo,
)
from app.services import embedding_service


def _fmt_dt(dt: datetime) -> str:
    return dt.isoformat()


@function_tool
async def list_available_slots(
    provider_name: str | None = None, days_ahead: int = 14
) -> dict:
    """List upcoming available appointment slots, optionally filtered by provider name.

    Args:
        provider_name: Optional substring match for provider name (e.g. "Chen").
        days_ahead: How many days into the future to search (default 14, max 30).
    """
    days_ahead = max(1, min(int(days_ahead or 14), 30))
    async with session_scope() as session:
        provider_id: uuid.UUID | None = None
        provider_label: str | None = None
        if provider_name:
            provider = await slot_repo.find_provider_by_name(session, provider_name)
            if provider is None:
                return {
                    "ok": False,
                    "error": f"No active provider matching '{provider_name}'.",
                    "slots": [],
                }
            provider_id = provider.id
            provider_label = provider.name

        slots = await slot_repo.list_available_slots(
            session,
            provider_id=provider_id,
            days_ahead=days_ahead,
            limit=20,
        )
        return {
            "ok": True,
            "provider_filter": provider_label,
            "slots": [
                {
                    "slot_id": s.slot_id,
                    "provider_id": s.provider_id,
                    "provider_name": s.provider_name,
                    "start_at": _fmt_dt(s.start_at),
                    "end_at": _fmt_dt(s.end_at),
                }
                for s in slots
            ],
        }


@function_tool
async def book_appointment(
    slot_id: str,
    patient_name: str,
    patient_email: str,
    patient_phone: str,
    reason: str,
) -> dict:
    """Book an available slot for the given patient. Returns appointment id on success.

    Args:
        slot_id: UUID of the slot returned by list_available_slots.
        patient_name: Full name of the patient.
        patient_email: Email address used for confirmation.
        patient_phone: Phone number (E.164 or local format).
        reason: Short visit reason (e.g. "Annual physical").
    """
    try:
        slot_uuid = uuid.UUID(slot_id)
    except (ValueError, TypeError):
        return {"ok": False, "error": "Invalid slot_id format."}

    async with session_scope() as session:
        slot = await slot_repo.get_slot(session, slot_uuid)
        if slot is None:
            return {"ok": False, "error": "Slot not found."}
        if slot.status != "available":
            return {"ok": False, "error": f"Slot is not available (status: {slot.status})."}

        appt = await appointment_repo.create_appointment(
            session,
            slot_id=slot_uuid,
            patient_name=patient_name.strip(),
            patient_email=patient_email.strip(),
            patient_phone=patient_phone.strip() if patient_phone else None,
            reason=reason.strip() if reason else None,
        )
        await slot_repo.mark_slot_status(session, slot_uuid, "booked")
        return {
            "ok": True,
            "appointment_id": str(appt.id),
            "slot_id": slot_id,
            "start_at": _fmt_dt(slot.start_at),
            "end_at": _fmt_dt(slot.end_at),
            "patient_name": appt.patient_name,
            "status": appt.status,
        }


@function_tool
async def cancel_appointment(appointment_id: str, reason: str | None = None) -> dict:
    """Cancel an existing appointment and free up its slot.

    Args:
        appointment_id: UUID of the appointment to cancel.
        reason: Optional cancellation reason recorded for analytics.
    """
    try:
        appt_uuid = uuid.UUID(appointment_id)
    except (ValueError, TypeError):
        return {"ok": False, "error": "Invalid appointment_id format."}

    async with session_scope() as session:
        pair = await appointment_repo.get_with_slot(session, appt_uuid)
        if pair is None:
            return {"ok": False, "error": "Appointment not found."}
        appt, slot = pair
        if appt.status == "cancelled":
            return {"ok": False, "error": "Appointment already cancelled."}

        await appointment_repo.cancel(session, appt_uuid, reason)
        await slot_repo.mark_slot_status(session, slot.id, "available")
        return {
            "ok": True,
            "appointment_id": appointment_id,
            "status": "cancelled",
            "freed_slot_id": str(slot.id),
        }


@function_tool
async def check_payer_accepted(payer_name: str) -> dict:
    """Check whether a payer/insurance company is accepted by the clinic.

    Args:
        payer_name: Exact or close payer name, e.g. "Blue Cross Blue Shield".
    """
    if not payer_name or not payer_name.strip():
        return {"ok": False, "error": "payer_name is required."}
    async with session_scope() as session:
        result = await insurance_repo.is_payer_accepted(session, payer_name)
        if result is None:
            return {
                "ok": True,
                "found": False,
                "payer_name": payer_name,
                "accepted": False,
                "message": "We don't have this payer on file. Please call the clinic to confirm.",
            }
        return {
            "ok": True,
            "found": True,
            "payer_name": result.payer_name,
            "plan_name": result.plan_name,
            "accepted": result.accepted,
            "notes": result.notes,
        }


@function_tool
async def verify_member(member_id: str) -> dict:
    """Verify a sample insurance member ID and return active coverage + copay.

    Args:
        member_id: Sample member id (e.g. "BCBS-X10001").
    """
    if not member_id or not member_id.strip():
        return {"ok": False, "error": "member_id is required."}
    async with session_scope() as session:
        result = await insurance_repo.verify_member(session, member_id)
        if result is None:
            return {
                "ok": True,
                "found": False,
                "member_id": member_id,
                "message": "Member id not found in our records.",
            }
        return {
            "ok": True,
            "found": True,
            "member_id": result.member_id,
            "member_name": result.member_name,
            "payer_name": result.payer_name,
            "plan_name": result.plan_name,
            "coverage_active": result.coverage_active,
            "copay_amount": float(result.copay_amount) if result.copay_amount is not None else None,
            "notes": result.notes,
        }


@function_tool
async def get_clinic_info() -> dict:
    """Return the clinic name, address, hours, contact info, and services offered."""
    async with session_scope() as session:
        clinic = await clinic_repo.get_clinic_settings(session)
        if clinic is None:
            return {"ok": False, "error": "Clinic settings not seeded."}
        return {
            "ok": True,
            "name": clinic.name,
            "address_line1": clinic.address_line1,
            "city": clinic.city,
            "state": clinic.state,
            "postal_code": clinic.postal_code,
            "phone": clinic.phone,
            "email": clinic.email,
            "timezone": clinic.timezone,
            "hours": clinic.hours_json,
            "services_offered": clinic.services_offered,
        }


@function_tool
async def search_clinic_faqs(query: str, k: int = 5) -> dict:
    """Semantic search over the clinic's FAQ knowledge base.

    Args:
        query: Natural-language question.
        k: How many top FAQs to return (default 5, max 10).
    """
    if not query or not query.strip():
        return {"ok": False, "error": "query is required."}
    k = max(1, min(int(k or 5), 10))
    embedding = await embedding_service.embed_text(query)
    async with session_scope() as session:
        hits = await faq_repo.search_faqs(session, embedding, k=k)
        return {
            "ok": True,
            "query": query,
            "results": [
                {
                    "question": h.question,
                    "answer": h.answer,
                    "tags": h.tags,
                    "distance": h.distance,
                }
                for h in hits
            ],
        }
