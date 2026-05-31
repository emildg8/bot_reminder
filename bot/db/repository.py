import logging
from datetime import datetime, time

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings
from bot.db.models import Base, ChatSettings, Reminder, ReminderEvent, User
from bot.services.reminder_utils import storage_next_run_at

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def dispose_engine() -> None:
    await engine.dispose()


logger = logging.getLogger(__name__)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
            if "mention_telegram_id" not in cols:
                await conn.execute(text("ALTER TABLE reminders ADD COLUMN mention_telegram_id BIGINT"))

            user_cols = {
                row[1]
                for row in (await conn.execute(text("PRAGMA table_info(users)"))).fetchall()
            }
            if "timezone_confirmed" not in user_cols:
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN timezone_confirmed BOOLEAN DEFAULT 1")
                )
            if "snooze_presets" not in user_cols:
                await conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN snooze_presets VARCHAR(64) "
                        "DEFAULT '5,15,30,60,180,240'"
                    )
                )
            if "snooze_step" not in user_cols:
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN snooze_step INTEGER DEFAULT 15")
                )

            chat_cols = {
                row[1]
                for row in (await conn.execute(text("PRAGMA table_info(chat_settings)"))).fetchall()
            }
            if "timezone_confirmed" not in chat_cols:
                await conn.execute(
                    text(
                        "ALTER TABLE chat_settings ADD COLUMN timezone_confirmed BOOLEAN DEFAULT 1"
                    )
                )

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
        except Exception as exc:
            logger.exception("Database migration failed")
            raise exc from exc


async def get_or_create_user(session: AsyncSession, telegram_id: int, timezone: str) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is not None:
        return user
    user = User(telegram_id=telegram_id, timezone=timezone, timezone_confirmed=False)
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one()


async def confirm_user_timezone(session: AsyncSession, user: User, timezone: str) -> User:
    user.timezone = timezone
    user.timezone_confirmed = True
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_timezone(session: AsyncSession, user: User, timezone: str) -> User:
    user.timezone = timezone
    user.timezone_confirmed = True
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_chat(session: AsyncSession, chat_id: int, timezone: str) -> ChatSettings:
    result = await session.execute(select(ChatSettings).where(ChatSettings.chat_id == chat_id))
    chat = result.scalar_one_or_none()
    if chat is not None:
        return chat
    chat = ChatSettings(chat_id=chat_id, timezone=timezone, timezone_confirmed=False)
    session.add(chat)
    try:
        await session.commit()
        await session.refresh(chat)
        return chat
    except IntegrityError:
        await session.rollback()
        result = await session.execute(select(ChatSettings).where(ChatSettings.chat_id == chat_id))
        return result.scalar_one()


async def update_chat_timezone(session: AsyncSession, chat: ChatSettings, timezone: str) -> ChatSettings:
    chat.timezone = timezone
    chat.timezone_confirmed = True
    await session.commit()
    await session.refresh(chat)
    return chat


async def set_chat_paused(session: AsyncSession, chat_id: int, paused: bool) -> ChatSettings:
    chat = await get_or_create_chat(session, chat_id, settings.default_timezone)
    chat.is_paused = paused
    await session.commit()
    await session.refresh(chat)
    return chat


async def is_chat_paused(session: AsyncSession, chat_id: int) -> bool:
    result = await session.execute(select(ChatSettings).where(ChatSettings.chat_id == chat_id))
    chat = result.scalar_one_or_none()
    return bool(chat and chat.is_paused)


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
    mention_telegram_id: int | None = None,
) -> Reminder:
    reminder = Reminder(
        user_id=user_id,
        chat_id=chat_id,
        created_by_telegram_id=created_by_telegram_id,
        mention_telegram_id=mention_telegram_id,
        timezone=timezone,
        text=text,
        kind=kind,
        next_run_at=storage_next_run_at(next_run_at, timezone),
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


async def get_active_chat_reminders(session: AsyncSession, chat_id: int) -> list[Reminder]:
    result = await session.execute(
        select(Reminder)
        .where(Reminder.chat_id == chat_id, Reminder.is_active.is_(True))
        .order_by(Reminder.created_at.desc())
    )
    return list(result.scalars().all())


async def search_chat_reminders(
    session: AsyncSession,
    chat_id: int,
    query: str,
    *,
    limit: int = 20,
) -> list[Reminder]:
    query = query.strip().lower()
    result = await session.execute(
        select(Reminder)
        .where(
            Reminder.chat_id == chat_id,
            Reminder.is_active.is_(True),
        )
        .order_by(Reminder.created_at.desc())
    )
    reminders = [r for r in result.scalars().all() if query in r.text.lower()]
    return reminders[:limit]


async def get_all_active_reminders(session: AsyncSession) -> list[Reminder]:
    result = await session.execute(
        select(Reminder).where(Reminder.is_active.is_(True)).order_by(Reminder.next_run_at)
    )
    return list(result.scalars().all())


async def update_reminder_next_run(
    session: AsyncSession, reminder: Reminder, next_run_at: datetime | None
) -> Reminder:
    if next_run_at is not None:
        next_run_at = storage_next_run_at(next_run_at, reminder.timezone)
    reminder.next_run_at = next_run_at
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def clear_reminder_next_run(session: AsyncSession, reminder: Reminder) -> Reminder:
    return await update_reminder_next_run(session, reminder, None)


async def deactivate_reminder(session: AsyncSession, reminder: Reminder) -> None:
    reminder.is_active = False
    await session.commit()


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def update_user_snooze_settings(
    session: AsyncSession,
    user: User,
    *,
    presets: str | None = None,
    step: int | None = None,
) -> User:
    if presets is not None:
        user.snooze_presets = presets
    if step is not None:
        user.snooze_step = step
    await session.commit()
    await session.refresh(user)
    return user


async def get_history_events_for_day(
    session: AsyncSession,
    chat_id: int,
    *,
    start: datetime,
    end: datetime,
    user_telegram_id: int | None = None,
    limit: int = 50,
) -> list[ReminderEvent]:
    query = (
        select(ReminderEvent)
        .where(
            ReminderEvent.chat_id == chat_id,
            ReminderEvent.event_at >= start,
            ReminderEvent.event_at < end,
        )
        .order_by(ReminderEvent.event_at.desc())
        .limit(limit)
    )
    if user_telegram_id is not None:
        query = query.where(ReminderEvent.user_telegram_id == user_telegram_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_inactive_chat_reminders(
    session: AsyncSession,
    chat_id: int,
    *,
    limit: int = 30,
    user_telegram_id: int | None = None,
) -> list[Reminder]:
    query = (
        select(Reminder)
        .where(Reminder.chat_id == chat_id, Reminder.is_active.is_(False))
        .order_by(Reminder.created_at.desc())
        .limit(limit)
    )
    if user_telegram_id is not None:
        query = query.where(Reminder.created_by_telegram_id == user_telegram_id)
    result = await session.execute(query)
    return list(result.scalars().all())


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
