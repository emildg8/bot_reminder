from datetime import datetime, time

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings
from bot.db.models import Base, Reminder, User

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # lightweight migration for existing SQLite DBs
        try:
            result = await conn.execute(text("PRAGMA table_info(reminders)"))
            cols = {row[1] for row in result.fetchall()}
            if "chat_id" not in cols:
                await conn.execute(text("ALTER TABLE reminders ADD COLUMN chat_id BIGINT"))
            if "created_by_telegram_id" not in cols:
                await conn.execute(text("ALTER TABLE reminders ADD COLUMN created_by_telegram_id BIGINT"))
            if "timezone" not in cols:
                await conn.execute(text("ALTER TABLE reminders ADD COLUMN timezone VARCHAR(64)"))
            if "weekdays_mask" not in cols:
                await conn.execute(text("ALTER TABLE reminders ADD COLUMN weekdays_mask INTEGER"))

            # Backfill for old rows (private chats): chat_id/user_id mapping.
            await conn.execute(
                text(
                    """
                    UPDATE reminders
                    SET chat_id = (SELECT telegram_id FROM users WHERE users.id = reminders.user_id)
                    WHERE chat_id IS NULL
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    UPDATE reminders
                    SET created_by_telegram_id = (SELECT telegram_id FROM users WHERE users.id = reminders.user_id)
                    WHERE created_by_telegram_id IS NULL
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    UPDATE reminders
                    SET timezone = (SELECT timezone FROM users WHERE users.id = reminders.user_id)
                    WHERE timezone IS NULL
                    """
                )
            )
        except Exception:
            # if the table doesn't exist yet or PRAGMA fails, create_all will handle it
            pass


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
    chat_id: int,
    created_by_telegram_id: int,
    timezone: str,
    text: str,
    kind: str,
    next_run_at: datetime | None = None,
    interval_seconds: int | None = None,
    daily_time: time | None = None,
    weekdays_mask: int | None = None,
) -> Reminder:
    reminder = Reminder(
        user_id=user_id,
        chat_id=chat_id,
        created_by_telegram_id=created_by_telegram_id,
        timezone=timezone,
        text=text,
        kind=kind,
        next_run_at=next_run_at,
        interval_seconds=interval_seconds,
        daily_time=daily_time,
        weekdays_mask=weekdays_mask,
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


async def get_active_chat_reminders(session: AsyncSession, chat_id: int) -> list[Reminder]:
    result = await session.execute(
        select(Reminder)
        .where(Reminder.chat_id == chat_id, Reminder.is_active.is_(True))
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


async def deactivate_all_chat_reminders(session: AsyncSession, chat_id: int) -> int:
    result = await session.execute(
        select(Reminder).where(Reminder.chat_id == chat_id, Reminder.is_active.is_(True))
    )
    reminders = list(result.scalars().all())
    for reminder in reminders:
        reminder.is_active = False
    if reminders:
        await session.commit()
    return len(reminders)
