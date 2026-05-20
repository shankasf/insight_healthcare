"""seed singleton clinic_settings, 3 providers, 1 plan, 3 members, 15 FAQs

Revision ID: 002_seed_static
Revises: 001_init
Create Date: 2026-05-20

"""
from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op

from scripts.seed_data import (
    CLINIC_FAQS,
    CLINIC_SETTINGS,
    INSURANCE_MEMBER_SAMPLES,
    INSURANCE_PLANS,
    PROVIDERS,
)

revision = "002_seed_static"
down_revision = "001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    clinic_payload = {
        **CLINIC_SETTINGS,
        "hours_json": json.dumps(CLINIC_SETTINGS["hours_json"]),
    }
    bind.execute(
        sa.text(
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
        clinic_payload,
    )

    for p in PROVIDERS:
        bind.execute(
            sa.text(
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

    for plan in INSURANCE_PLANS:
        bind.execute(
            sa.text(
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
        bind.execute(
            sa.text(
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

    # FAQs use natural-key dedupe on question text so re-run is idempotent.
    for faq in CLINIC_FAQS:
        bind.execute(
            sa.text(
                """
                INSERT INTO clinic_faqs (question, answer, tags, active)
                SELECT :question, :answer, :tags, true
                WHERE NOT EXISTS (
                    SELECT 1 FROM clinic_faqs WHERE question = :question
                );
                """
            ),
            {
                "question": faq["question"],
                "answer": faq["answer"],
                "tags": faq["tags"],
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM clinic_faqs;"))
    bind.execute(sa.text("DELETE FROM insurance_member_samples;"))
    bind.execute(sa.text("DELETE FROM insurance_plans;"))
    bind.execute(sa.text("DELETE FROM providers;"))
    bind.execute(sa.text("DELETE FROM clinic_settings;"))
