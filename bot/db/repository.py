from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings
from bot.db.models import Base, Reminder, User

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_or_create_user(session: AsyncSession, telegram_id: int, timezone: str) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, timezone=timezone)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def update_user_timezone(session: AsyncSession, user: User, timezone: str) -> User:
    user.timezone = timezone
    await session.commit()
    await session.refresh(user)
    return user


async def create_reminder(
    session: AsyncSession,
    user_id: int,
    text: str,
    kind: str,
    next_run_at: datetime | None = None,
    interval_seconds: int | None = None,
    daily_time: time | None = None,
) -> Reminder:
    reminder = Reminder(
        user_id=user_id,
        text=text,
        kind=kind,
        next_run_at=next_run_at,
        interval_seconds=interval_seconds,
        daily_time=daily_time,
    )
    session.add(reminder)
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def get_reminder(session: AsyncSession, reminder_id: int) -> Reminder | None:
    result = await session.execute(select(Reminder).where(Reminder.id == reminder_id))
    return result.scalar_one_or_none()


async def get_active_reminders(session: AsyncSession, user_id: int) -> list[Reminder]:
    result = await session.execute(
        select(Reminder)
        .where(Reminder.user_id == user_id, Reminder.is_active.is_(True))
        .order_by(Reminder.created_at.desc())
    )
    return list(result.scalars().all())


async def get_all_active_reminders(session: AsyncSession) -> list[Reminder]:
    result = await session.execute(
        select(Reminder).where(Reminder.is_active.is_(True)).order_by(Reminder.next_run_at)
    )
    return list(result.scalars().all())


async def update_reminder_next_run(session: AsyncSession, reminder: Reminder, next_run_at: datetime) -> Reminder:
    reminder.next_run_at = next_run_at
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def deactivate_reminder(session: AsyncSession, reminder: Reminder) -> None:
    reminder.is_active = False
    await session.commit()
