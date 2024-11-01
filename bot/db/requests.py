from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as upsert
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


async def add_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: str,
    last_name: str | None = None,
):

    stmt = upsert(User).values(
        {
            "telegram_id": telegram_id,
            "first_name": first_name,
            "last_name": last_name,
        }
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=['telegram_id'],
        set_=dict(
            first_name=first_name,
            last_name=last_name,
        ),
    )
    await session.execute(stmt)
    await session.commit()


async def get_nickname(
    session: AsyncSession,
    telegram_id: int,
):
    async with session.begin():
        stmt = select(User.nickname).where(
            User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        nickname = result.scalar()
    return nickname


async def registrate_user(
    session: AsyncSession,
    telegram_id: int,
    nickname: str,
    guests: int
):
    stmt = update(User).where(
        User.telegram_id == telegram_id).values(
        nickname=nickname,
        guests=guests)
    await session.execute(stmt)
    await session.commit()


async def unregistrate_user(
    session: AsyncSession,
    telegram_id: int,
):
    stmt = update(User).where(
        User.telegram_id == telegram_id).values(
        guests=0)
    await session.execute(stmt)
    await session.commit()


async def get_is_registered(
    session: AsyncSession,
    telegram_id: int,
):
    async with session.begin():
        stmt = select(User.guests).where(
            User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        is_registered = result.scalar()
    return is_registered


async def count_registered(
    session: AsyncSession,
):
    stmt = select(func.sum(User.guests))
    result = await session.execute(stmt)
    await session.commit()
    guests = result.scalar_one()
    return guests


async def guest_list(
    session: AsyncSession
):
    stmt = select(
        User.nickname,
        User.guests
    ).where(
        User.guests != 0
    ).order_by(
        User.nickname
    )
    result = await session.execute(stmt)
    await session.commit()
    guest_list = result.fetchall()
    return guest_list
