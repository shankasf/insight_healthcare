from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import ClinicFaq


@dataclass(slots=True)
class FaqHit:
    question: str
    answer: str
    tags: list[str] | None
    distance: float


async def search_faqs(
    session: AsyncSession, query_embedding: list[float], k: int = 5
) -> list[FaqHit]:
    distance = ClinicFaq.embedding.cosine_distance(query_embedding).label("distance")
    stmt = (
        select(ClinicFaq.question, ClinicFaq.answer, ClinicFaq.tags, distance)
        .where(ClinicFaq.active.is_(True))
        .where(ClinicFaq.embedding.is_not(None))
        .order_by(distance.asc())
        .limit(k)
    )
    rows = (await session.execute(stmt)).all()
    return [
        FaqHit(question=r.question, answer=r.answer, tags=r.tags, distance=float(r.distance))
        for r in rows
    ]


async def list_faqs_missing_embedding(session: AsyncSession) -> list[ClinicFaq]:
    stmt = select(ClinicFaq).where(ClinicFaq.embedding.is_(None)).order_by(ClinicFaq.created_at.asc())
    return list((await session.execute(stmt)).scalars().all())
