from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.dto.create_channels import CreateChannel


async def get_create_channels(session: AsyncSession, server_id: int) -> list[int]:
    stmt = select(CreateChannel.id).filter(CreateChannel.server_id == server_id)
    res = (await session.execute(stmt)).all()
    return [channel[0] for channel in res]


async def get_create_channel(
    session: AsyncSession, server_id: int, channel_id: int
) -> CreateChannel | None:
    stmt = (
        select(CreateChannel)
        .filter(CreateChannel.id == channel_id)
        .filter(CreateChannel.server_id == server_id)
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_create_channel(session: AsyncSession, server_id: int, channel_id: int):
    channel = dict(server_id=server_id, id=channel_id)
    stmt = insert(CreateChannel).values(channel)
    try:
        await session.execute(stmt)
        await session.commit()
    except IntegrityError:
        pass


async def remove_create_channel(session: AsyncSession, server_id: int, channel_id: int):
    voice_channel = await get_create_channel(session, server_id, channel_id)
    await session.delete(voice_channel)
    await session.commit()
