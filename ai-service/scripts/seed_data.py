"""Single source of truth for deterministic seed data.

Imported by both the alembic migrations (002, 003) and scripts/seed_clinic.py so
the demo data is identical regardless of how it's loaded.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

# Fixed UUIDs so re-running seed_clinic.py is idempotent (ON CONFLICT DO UPDATE).
CLINIC_TZ = "America/Chicago"

PROVIDER_CHEN_ID = uuid.UUID("a0000001-0000-0000-0000-000000000001")
PROVIDER_THOMPSON_ID = uuid.UUID("a0000002-0000-0000-0000-000000000002")
PROVIDER_PATEL_ID = uuid.UUID("a0000003-0000-0000-0000-000000000003")

INSURANCE_PLAN_ID = uuid.UUID("b0000001-0000-0000-0000-000000000001")

MEMBER_SAMPLE_IDS = {
    "BCBS-X10001": uuid.UUID("c0000001-0000-0000-0000-000000000001"),
    "BCBS-X10002": uuid.UUID("c0000002-0000-0000-0000-000000000002"),
    "BCBS-X10003": uuid.UUID("c0000003-0000-0000-0000-000000000003"),
}


CLINIC_SETTINGS = {
    "id": 1,
    "name": "Insight Healthcare Clinic",
    "address_line1": "123 Wellness Way, Suite 200",
    "city": "Springfield",
    "state": "IL",
    "postal_code": "62701",
    "phone": "(555) 555-0100",
    "email": "hello@insighthealth.example",
    "timezone": CLINIC_TZ,
    "hours_json": {
        "mon": "09:00-17:00",
        "tue": "09:00-17:00",
        "wed": "09:00-17:00",
        "thu": "09:00-17:00",
        "fri": "09:00-17:00",
        "sat": "closed",
        "sun": "closed",
    },
    "services_offered": [
        "Annual physicals",
        "Sick visits",
        "Immunizations",
        "Chronic disease management",
        "Wellness screenings",
        "Telehealth",
        "Basic lab work",
    ],
}


PROVIDERS = [
    {
        "id": PROVIDER_CHEN_ID,
        "name": "Dr. Sarah Chen",
        "role": "Family Medicine",
        "email": "s.chen@insighthealth.example",
        "phone": None,
        "active": True,
    },
    {
        "id": PROVIDER_THOMPSON_ID,
        "name": "Dr. Marcus Thompson",
        "role": "Family Medicine",
        "email": "m.thompson@insighthealth.example",
        "phone": None,
        "active": True,
    },
    {
        "id": PROVIDER_PATEL_ID,
        "name": "Dr. Priya Patel",
        "role": "Family Medicine",
        "email": "p.patel@insighthealth.example",
        "phone": None,
        "active": True,
    },
]


INSURANCE_PLANS = [
    {
        "id": INSURANCE_PLAN_ID,
        "payer_name": "Blue Cross Blue Shield",
        "plan_name": "PPO",
        "accepted": True,
        "notes": "In-network. Most BCBS PPO plans accepted; bring card at first visit.",
        "effective_from": None,
        "effective_to": None,
    }
]


INSURANCE_MEMBER_SAMPLES = [
    {
        "id": MEMBER_SAMPLE_IDS["BCBS-X10001"],
        "plan_id": INSURANCE_PLAN_ID,
        "member_id": "BCBS-X10001",
        "member_name": "John Doe",
        "coverage_active": True,
        "copay_amount": 25,
        "effective_from": None,
        "effective_to": None,
        "notes": "Standard PPO Gold",
    },
    {
        "id": MEMBER_SAMPLE_IDS["BCBS-X10002"],
        "plan_id": INSURANCE_PLAN_ID,
        "member_id": "BCBS-X10002",
        "member_name": "Jane Smith",
        "coverage_active": True,
        "copay_amount": 40,
        "effective_from": None,
        "effective_to": None,
        "notes": "High-deductible PPO",
    },
    {
        "id": MEMBER_SAMPLE_IDS["BCBS-X10003"],
        "plan_id": INSURANCE_PLAN_ID,
        "member_id": "BCBS-X10003",
        "member_name": "Bob Johnson",
        "coverage_active": False,
        "copay_amount": None,
        "effective_from": None,
        "effective_to": date(2025, 12, 31),
        "notes": "Coverage ended 2025-12-31 (expired)",
    },
]


CLINIC_FAQS: list[dict] = [
    {
        "question": "What are your hours?",
        "answer": "We're open Monday through Friday, 9:00 AM to 5:00 PM. Closed Saturday and Sunday.",
        "tags": ["hours", "schedule"],
    },
    {
        "question": "Where are you located?",
        "answer": "123 Wellness Way, Suite 200, Springfield, IL 62701.",
        "tags": ["location", "address"],
    },
    {
        "question": "Is parking available?",
        "answer": "Yes — we have a free on-site lot with accessible spots near the entrance.",
        "tags": ["parking", "accessibility"],
    },
    {
        "question": "What services do you offer?",
        "answer": (
            "Family medicine: annual physicals, sick visits, immunizations, chronic-disease "
            "management, wellness screenings, telehealth, and basic lab work."
        ),
        "tags": ["services"],
    },
    {
        "question": "Do you treat children?",
        "answer": "Yes — we see patients ages 6 months and up.",
        "tags": ["pediatrics", "services"],
    },
    {
        "question": "Do you offer telehealth?",
        "answer": "Yes, telehealth appointments are available Monday through Friday, 10 AM to 3 PM.",
        "tags": ["telehealth", "services"],
    },
    {
        "question": "What insurance do you accept?",
        "answer": "We're in-network with Blue Cross Blue Shield PPO. Other plans considered case-by-case.",
        "tags": ["insurance"],
    },
    {
        "question": "How do I book an appointment?",
        "answer": "You can book right here in this chat, or call us at (555) 555-0100.",
        "tags": ["booking", "appointments"],
    },
    {
        "question": "How do I reschedule or cancel?",
        "answer": (
            "Use this chatbot or call us. We appreciate at least 24 hours' notice when possible."
        ),
        "tags": ["booking", "appointments", "cancel"],
    },
    {
        "question": "What should I bring to my first visit?",
        "answer": (
            "Photo ID, insurance card, a list of current medications, and any prior medical records "
            "you have."
        ),
        "tags": ["new patient", "first visit"],
    },
    {
        "question": "What if I'm running late?",
        "answer": "Please call us. If you're more than 15 minutes late we may need to reschedule.",
        "tags": ["late", "policy"],
    },
    {
        "question": "Do you do lab work on-site?",
        "answer": "Yes — we handle basic blood draws and urinalysis in the clinic.",
        "tags": ["lab", "services"],
    },
    {
        "question": "Can I see the same provider every time?",
        "answer": "Yes — just request your preferred provider when booking.",
        "tags": ["providers"],
    },
    {
        "question": "How long is a typical visit?",
        "answer": "About 30 minutes for routine visits, and 45 minutes for new-patient visits.",
        "tags": ["visit", "duration"],
    },
    {
        "question": "How do I get a prescription refill?",
        "answer": (
            "Have your pharmacy fax or e-request us. We respond within 24 business hours."
        ),
        "tags": ["prescriptions", "refill"],
    },
]


@dataclass(slots=True, frozen=True)
class SlotRow:
    provider_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    status: str


@dataclass(slots=True, frozen=True)
class AppointmentSeed:
    provider_id: uuid.UUID
    days_ahead: int
    local_hour: int
    local_minute: int
    patient_name: str
    patient_email: str
    patient_phone: str
    reason: str


SAMPLE_APPOINTMENTS: list[AppointmentSeed] = [
    AppointmentSeed(
        provider_id=PROVIDER_CHEN_ID,
        days_ahead=1,
        local_hour=10,
        local_minute=0,
        patient_name="John Doe",
        patient_email="john.doe@example.com",
        patient_phone="(555) 555-0111",
        reason="Annual physical",
    ),
    AppointmentSeed(
        provider_id=PROVIDER_THOMPSON_ID,
        days_ahead=2,
        local_hour=14,
        local_minute=0,
        patient_name="Jane Smith",
        patient_email="jane.smith@example.com",
        patient_phone="(555) 555-0122",
        reason="Diabetes follow-up",
    ),
    AppointmentSeed(
        provider_id=PROVIDER_PATEL_ID,
        days_ahead=5,
        local_hour=11,
        local_minute=30,
        patient_name="Bob Johnson",
        patient_email="bob.j@example.com",
        patient_phone="(555) 555-0133",
        reason="Sore throat — sick visit",
    ),
]


def generate_slots(now: datetime | None = None) -> list[SlotRow]:
    """Generate the next 14 weekdays of 30-min slots from 09:00 to 17:00 local time per provider.

    Lunch (12:00-13:00) is marked 'blocked'. Everything else is 'available'.
    The 3 specific slots matching SAMPLE_APPOINTMENTS will be flipped to 'booked' later
    after appointments are inserted.
    """
    tz = ZoneInfo(CLINIC_TZ)
    base_local_date = (now.astimezone(tz).date() if now else datetime.now(tz).date())

    slots: list[SlotRow] = []
    for provider in PROVIDERS:
        provider_id = provider["id"]
        for day_offset in range(0, 14):
            d = base_local_date + timedelta(days=day_offset)
            if d.weekday() >= 5:  # Sat=5, Sun=6
                continue
            for hour in range(9, 17):
                for minute in (0, 30):
                    start_local = datetime.combine(d, time(hour, minute), tzinfo=tz)
                    end_local = start_local + timedelta(minutes=30)
                    status = "blocked" if hour == 12 else "available"
                    slots.append(
                        SlotRow(
                            provider_id=provider_id,
                            start_at=start_local.astimezone(ZoneInfo("UTC")),
                            end_at=end_local.astimezone(ZoneInfo("UTC")),
                            status=status,
                        )
                    )
    return slots


def appointment_slot_target(appt: AppointmentSeed, now: datetime | None = None) -> datetime:
    tz = ZoneInfo(CLINIC_TZ)
    base_local_date = (now.astimezone(tz).date() if now else datetime.now(tz).date())
    target_date = base_local_date + timedelta(days=appt.days_ahead)
    start_local = datetime.combine(
        target_date, time(appt.local_hour, appt.local_minute), tzinfo=tz
    )
    return start_local.astimezone(ZoneInfo("UTC"))
