import time
import uuid
from datetime import datetime
from typing import Any

from agents import function_tool

from app.core.db import session_scope
from app.core.logging import get_logger
from app.repositories import (
    appointment_repo,
    clinic_repo,
    faq_repo,
    insurance_repo,
    slot_repo,
)
from app.services import embedding_service

_tool_log = get_logger("agent.tools")


def _fmt_dt(dt: datetime) -> str:
    return dt.isoformat()


def _trim(value: Any, max_len: int = 160) -> str:
    s = "" if value is None else str(value)
    return s if len(s) <= max_len else s[:max_len] + "..."


def _summarize_result(name: str, result: Any) -> str:
    if not isinstance(result, dict):
        return _trim(result)
    if not result.get("ok", True):
        return f"ok=False error={_trim(result.get('error'))}"
    if name == "list_available_slots":
        return f"slots={len(result.get('slots') or [])} provider_filter={result.get('provider_filter')}"
    if name == "book_appointment":
        return f"appointment_id={result.get('appointment_id')} status={result.get('status')}"
    if name == "cancel_appointment":
        return f"appointment_id={result.get('appointment_id')} status={result.get('status')} freed_slot={result.get('freed_slot_id')}"
    if name == "check_payer_accepted":
        return f"payer={result.get('payer_name')} found={result.get('found')} accepted={result.get('accepted')}"
    if name == "verify_member":
        return f"member_id={result.get('member_id')} found={result.get('found')} active={result.get('coverage_active')} copay={result.get('copay_amount')}"
    if name == "get_clinic_info":
        return f"name={result.get('name')} services={len(result.get('services_offered') or [])}"
    if name == "search_clinic_faqs":
        hits = result.get("results") or []
        top = hits[0].get("question") if hits else None
        return f"hits={len(hits)} top={_trim(top, 80)}"
    return _trim(result)


def _begin(name: str, args: dict[str, Any]) -> float:
    _tool_log.info("tool_call name=%s args=%s", name, _trim(args, 220))
    return time.monotonic()


def _end(name: str, start: float, result: Any) -> None:
    latency_ms = int((time.monotonic() - start) * 1000)
    ok = result.get("ok", True) if isinstance(result, dict) else True
    _tool_log.info(
        "tool_done name=%s ok=%s latency_ms=%d summary=%s",
        name, ok, latency_ms, _summarize_result(name, result),
    )


def _emit(name: str, start: float, result: Any) -> Any:
    """Log tool completion and return the result. Use as `return _emit(...)`."""
    _end(name, start, result)
    return result


@function_tool
async def list_available_slots(
    provider_name: str | None = None, days_ahead: int = 14
) -> dict:
    """List upcoming available appointment slots, optionally filtered by provider name.

    Args:
        provider_name: Optional substring match for provider name (e.g. "Chen").
        days_ahead: How many days into the future to search (default 14, max 30).
    """
    _t = _begin("list_available_slots", {"provider_name": provider_name, "days_ahead": days_ahead})
    days_ahead = max(1, min(int(days_ahead or 14), 30))
    async with session_scope() as session:
        provider_id: uuid.UUID | None = None
        provider_label: str | None = None
        if provider_name:
            provider = await slot_repo.find_provider_by_name(session, provider_name)
            if provider is None:
                return _emit("list_available_slots", _t, {
                    "ok": False,
                    "error": f"No active provider matching '{provider_name}'.",
                    "slots": [],
                })
            provider_id = provider.id
            provider_label = provider.name

        slots = await slot_repo.list_available_slots(
            session,
            provider_id=provider_id,
            days_ahead=days_ahead,
            limit=20,
        )
        return _emit("list_available_slots", _t, {
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
        })


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
    _t = _begin("book_appointment", {
        "slot_id": slot_id, "patient_name": patient_name,
        "patient_email": patient_email, "patient_phone": patient_phone,
        "reason": reason,
    })
    try:
        slot_uuid = uuid.UUID(slot_id)
    except (ValueError, TypeError):
        return _emit("book_appointment", _t, {"ok": False, "error": "Invalid slot_id format."})

    async with session_scope() as session:
        slot = await slot_repo.get_slot(session, slot_uuid)
        if slot is None:
            return _emit("book_appointment", _t, {"ok": False, "error": "Slot not found."})
        if slot.status != "available":
            return _emit("book_appointment", _t, {"ok": False, "error": f"Slot is not available (status: {slot.status})."})

        appt = await appointment_repo.create_appointment(
            session,
            slot_id=slot_uuid,
            patient_name=patient_name.strip(),
            patient_email=patient_email.strip(),
            patient_phone=patient_phone.strip() if patient_phone else None,
            reason=reason.strip() if reason else None,
        )
        await slot_repo.mark_slot_status(session, slot_uuid, "booked")
        return _emit("book_appointment", _t, {
            "ok": True,
            "appointment_id": str(appt.id),
            "slot_id": slot_id,
            "start_at": _fmt_dt(slot.start_at),
            "end_at": _fmt_dt(slot.end_at),
            "patient_name": appt.patient_name,
            "status": appt.status,
        })


@function_tool
async def cancel_appointment(appointment_id: str, reason: str | None = None) -> dict:
    """Cancel an existing appointment and free up its slot.

    Args:
        appointment_id: UUID of the appointment to cancel.
        reason: Optional cancellation reason recorded for analytics.
    """
    _t = _begin("cancel_appointment", {"appointment_id": appointment_id, "reason": reason})
    try:
        appt_uuid = uuid.UUID(appointment_id)
    except (ValueError, TypeError):
        return _emit("cancel_appointment", _t, {"ok": False, "error": "Invalid appointment_id format."})

    async with session_scope() as session:
        pair = await appointment_repo.get_with_slot(session, appt_uuid)
        if pair is None:
            return _emit("cancel_appointment", _t, {"ok": False, "error": "Appointment not found."})
        appt, slot = pair
        if appt.status == "cancelled":
            return _emit("cancel_appointment", _t, {"ok": False, "error": "Appointment already cancelled."})

        await appointment_repo.cancel(session, appt_uuid, reason)
        await slot_repo.mark_slot_status(session, slot.id, "available")
        return _emit("cancel_appointment", _t, {
            "ok": True,
            "appointment_id": appointment_id,
            "status": "cancelled",
            "freed_slot_id": str(slot.id),
        })


@function_tool
async def check_payer_accepted(payer_name: str) -> dict:
    """Check whether a payer/insurance company is accepted by the clinic.

    Args:
        payer_name: Exact or close payer name, e.g. "Blue Cross Blue Shield".
    """
    _t = _begin("check_payer_accepted", {"payer_name": payer_name})
    if not payer_name or not payer_name.strip():
        return _emit("check_payer_accepted", _t, {"ok": False, "error": "payer_name is required."})
    async with session_scope() as session:
        result = await insurance_repo.is_payer_accepted(session, payer_name)
        if result is None:
            return _emit("check_payer_accepted", _t, {
                "ok": True,
                "found": False,
                "payer_name": payer_name,
                "accepted": False,
                "message": "We don't have this payer on file. Please call the clinic to confirm.",
            })
        return _emit("check_payer_accepted", _t, {
            "ok": True,
            "found": True,
            "payer_name": result.payer_name,
            "plan_name": result.plan_name,
            "accepted": result.accepted,
            "notes": result.notes,
        })


@function_tool
async def verify_member(member_id: str) -> dict:
    """Verify a sample insurance member ID and return active coverage + copay.

    Args:
        member_id: Sample member id (e.g. "BCBS-X10001").
    """
    _t = _begin("verify_member", {"member_id": member_id})
    if not member_id or not member_id.strip():
        return _emit("verify_member", _t, {"ok": False, "error": "member_id is required."})
    async with session_scope() as session:
        result = await insurance_repo.verify_member(session, member_id)
        if result is None:
            return _emit("verify_member", _t, {
                "ok": True,
                "found": False,
                "member_id": member_id,
                "message": "Member id not found in our records.",
            })
        return _emit("verify_member", _t, {
            "ok": True,
            "found": True,
            "member_id": result.member_id,
            "member_name": result.member_name,
            "payer_name": result.payer_name,
            "plan_name": result.plan_name,
            "coverage_active": result.coverage_active,
            "copay_amount": float(result.copay_amount) if result.copay_amount is not None else None,
            "notes": result.notes,
        })


@function_tool
async def get_clinic_info() -> dict:
    """Return the clinic name, address, hours, contact info, and services offered."""
    _t = _begin("get_clinic_info", {})
    async with session_scope() as session:
        clinic = await clinic_repo.get_clinic_settings(session)
        if clinic is None:
            return _emit("get_clinic_info", _t, {"ok": False, "error": "Clinic settings not seeded."})
        return _emit("get_clinic_info", _t, {
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
        })


@function_tool
async def search_clinic_faqs(query: str, k: int = 5) -> dict:
    """Semantic search over the clinic's FAQ knowledge base.

    Args:
        query: Natural-language question.
        k: How many top FAQs to return (default 5, max 10).
    """
    _t = _begin("search_clinic_faqs", {"query": query, "k": k})
    if not query or not query.strip():
        return _emit("search_clinic_faqs", _t, {"ok": False, "error": "query is required."})
    k = max(1, min(int(k or 5), 10))
    embedding = await embedding_service.embed_text(query)
    async with session_scope() as session:
        hits = await faq_repo.search_faqs(session, embedding, k=k)
        return _emit("search_clinic_faqs", _t, {
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
        })
