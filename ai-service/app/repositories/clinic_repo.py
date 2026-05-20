from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import ClinicSettings


async def get_clinic_settings(session: AsyncSession) -> ClinicSettings | None:
    return await session.get(ClinicSettings, 1)
