"""init schema: 9 tables + extensions + indexes

Revision ID: 001_init
Revises:
Create Date: 2026-05-20

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        "clinic_settings",
        sa.Column("id", sa.SmallInteger(), primary_key=True, autoincrement=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("address_line1", sa.Text()),
        sa.Column("city", sa.Text()),
        sa.Column("state", sa.Text()),
        sa.Column("postal_code", sa.Text()),
        sa.Column("phone", sa.Text()),
        sa.Column("email", sa.Text()),
        sa.Column("timezone", sa.Text(), nullable=False, server_default="America/Chicago"),
        sa.Column("hours_json", postgresql.JSONB()),
        sa.Column("services_offered", postgresql.ARRAY(sa.String())),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("id = 1", name="ck_clinic_settings_singleton"),
    )

    op.create_table(
        "providers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("role", sa.Text()),
        sa.Column("email", sa.Text()),
        sa.Column("phone", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "appointment_slots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("providers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="available"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('available','booked','blocked')", name="ck_appointment_slots_status"
        ),
    )
    op.create_index(
        "ix_appointment_slots_status_start", "appointment_slots", ["status", "start_at"]
    )
    op.create_index(
        "ix_appointment_slots_provider_start",
        "appointment_slots",
        ["provider_id", "start_at"],
    )

    op.create_table(
        "appointments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("appointment_slots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("patient_name", sa.Text(), nullable=False),
        sa.Column("patient_email", sa.Text(), nullable=False),
        sa.Column("patient_phone", sa.Text()),
        sa.Column("reason", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="scheduled"),
        sa.Column("cancellation_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("slot_id", name="uq_appointments_slot_id"),
        sa.CheckConstraint(
            "status IN ('scheduled','completed','cancelled','no_show')",
            name="ck_appointments_status",
        ),
    )

    op.create_table(
        "insurance_plans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("payer_name", sa.Text(), nullable=False),
        sa.Column("plan_name", sa.Text()),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text()),
        sa.Column("effective_from", sa.Date()),
        sa.Column("effective_to", sa.Date()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_insurance_plans_payer_lower",
        "insurance_plans",
        [sa.text("lower(payer_name)")],
    )

    op.create_table(
        "insurance_member_samples",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("insurance_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("member_id", sa.Text(), nullable=False),
        sa.Column("member_name", sa.Text(), nullable=False),
        sa.Column("coverage_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("copay_amount", sa.Numeric(10, 2)),
        sa.Column("effective_from", sa.Date()),
        sa.Column("effective_to", sa.Date()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("member_id", name="uq_insurance_member_samples_member_id"),
    )

    op.create_table(
        "clinic_faqs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String())),
        sa.Column("embedding", Vector(1536)),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    # IVFFlat with lists=100 — reasonable starter for <10k rows; bump on larger corpora.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_clinic_faqs_embedding "
        "ON clinic_faqs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
    )

    op.create_table(
        "chat_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("session_key", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "last_message_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("user_agent", sa.Text()),
        sa.Column("ip_hash", sa.Text()),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("session_key", name="uq_chat_sessions_session_key"),
    )

    op.create_table(
        "chat_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_used", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tool_calls_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "agent_used IN ('triage','appointment','insurance','knowledge','out_of_scope')",
            name="ck_chat_events_agent_used",
        ),
    )
    op.create_index(
        "ix_chat_events_session_created", "chat_events", ["session_id", "created_at"]
    )
    op.create_index("ix_chat_events_created", "chat_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_chat_events_created", table_name="chat_events")
    op.drop_index("ix_chat_events_session_created", table_name="chat_events")
    op.drop_table("chat_events")
    op.drop_table("chat_sessions")
    op.execute("DROP INDEX IF EXISTS ix_clinic_faqs_embedding;")
    op.drop_table("clinic_faqs")
    op.drop_table("insurance_member_samples")
    op.drop_index("ix_insurance_plans_payer_lower", table_name="insurance_plans")
    op.drop_table("insurance_plans")
    op.drop_table("appointments")
    op.drop_index("ix_appointment_slots_provider_start", table_name="appointment_slots")
    op.drop_index("ix_appointment_slots_status_start", table_name="appointment_slots")
    op.drop_table("appointment_slots")
    op.drop_table("providers")
    op.drop_table("clinic_settings")
