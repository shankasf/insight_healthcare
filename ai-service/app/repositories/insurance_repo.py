from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insurance import InsuranceMemberSample, InsurancePlan


@dataclass(slots=True)
class PayerLookup:
    payer_name: str
    plan_name: str | None
    accepted: bool
    notes: str | None


@dataclass(slots=True)
class MemberLookup:
    member_id: str
    member_name: str
    payer_name: str
    plan_name: str | None
    coverage_active: bool
    copay_amount: Decimal | None
    notes: str | None


async def is_payer_accepted(session: AsyncSession, payer_name: str) -> PayerLookup | None:
    stmt = select(InsurancePlan).where(
        func.lower(InsurancePlan.payer_name) == payer_name.strip().lower()
    )
    plan = (await session.execute(stmt)).scalars().first()
    if plan is None:
        return None
    return PayerLookup(
        payer_name=plan.payer_name,
        plan_name=plan.plan_name,
        accepted=plan.accepted,
        notes=plan.notes,
    )


async def verify_member(session: AsyncSession, member_id: str) -> MemberLookup | None:
    stmt = (
        select(InsuranceMemberSample, InsurancePlan)
        .join(InsurancePlan, InsurancePlan.id == InsuranceMemberSample.plan_id)
        .where(InsuranceMemberSample.member_id == member_id.strip())
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    member, plan = row
    return MemberLookup(
        member_id=member.member_id,
        member_name=member.member_name,
        payer_name=plan.payer_name,
        plan_name=plan.plan_name,
        coverage_active=member.coverage_active,
        copay_amount=member.copay_amount,
        notes=member.notes,
    )
