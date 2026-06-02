import logging
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import BASE_DIR, settings
from bot.db.models import AdminAction, BroadcastDraft, ChatSettings, Reminder, ReminderEvent, ReminderEventKind, StarPayment, User
from bot.services.reminder_utils import storage_next_run_at

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def dispose_engine() -> None:
    await engine.dispose()


logger = logging.getLogger(__name__)


async def init_db() -> None:
    from bot.db.migrate import init_db_migrations

    if settings.database_url.startswith("sqlite"):
        raw = settings.database_url.split("///", 1)[-1]
        path = Path(raw)
        if not path.is_absolute():
            path = BASE_DIR / raw.lstrip("./")
        path.parent.mkdir(parents=True, exist_ok=True)

    await init_db_migrations()


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


async def complete_user_onboarding(session: AsyncSession, user: User) -> User:
    user.onboarding_done = True
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


async def update_channel_linked_chat(
    session: AsyncSession, channel_id: int, linked_chat_id: int | None
) -> None:
    result = await session.execute(
        select(ChatSettings).where(ChatSettings.chat_id == channel_id)
    )
    chat = result.scalar_one_or_none()
    if chat is None:
        return
    chat.linked_chat_id = linked_chat_id
    await session.commit()


async def find_channel_by_linked_chat(
    session: AsyncSession, discussion_chat_id: int
) -> int | None:
    result = await session.execute(
        select(ChatSettings.chat_id).where(
            ChatSettings.linked_chat_id == discussion_chat_id
        )
    )
    row = result.scalar_one_or_none()
    return int(row) if row is not None else None


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


async def update_reminder_telegram_schedule(
    session: AsyncSession, reminder: Reminder, message_id: int | None
) -> Reminder:
    reminder.telegram_schedule_message_id = message_id
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


async def count_active_reminders_for_user(session: AsyncSession, telegram_id: int) -> int:
    result = await session.execute(
        select(Reminder).where(
            Reminder.created_by_telegram_id == telegram_id,
            Reminder.is_active.is_(True),
        )
    )
    return len(list(result.scalars().all()))


async def set_user_pro(
    session: AsyncSession,
    telegram_id: int,
    *,
    is_pro: bool,
    pro_expires_at: datetime | None = None,
) -> User | None:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is None:
        return None
    user.is_pro = is_pro
    user.pro_expires_at = pro_expires_at if is_pro else None
    await session.commit()
    await session.refresh(user)
    return user


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


async def insert_admin_action(session: AsyncSession, admin_id: int, action: str) -> AdminAction:
    row = AdminAction(admin_telegram_id=admin_id, action=action[:512])
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def fetch_admin_actions(session: AsyncSession, *, limit: int = 15) -> list[AdminAction]:
    result = await session.execute(
        select(AdminAction).order_by(AdminAction.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def upsert_broadcast_draft(
    session: AsyncSession,
    admin_id: int,
    text: str,
    *,
    filter: str = "all",
) -> BroadcastDraft:
    result = await session.execute(
        select(BroadcastDraft).where(BroadcastDraft.admin_telegram_id == admin_id)
    )
    draft = result.scalar_one_or_none()
    if draft is None:
        draft = BroadcastDraft(admin_telegram_id=admin_id, text=text, filter=filter)
        session.add(draft)
    else:
        draft.text = text
        draft.filter = filter
    await session.commit()
    await session.refresh(draft)
    return draft


async def get_broadcast_draft(session: AsyncSession, admin_id: int) -> BroadcastDraft | None:
    result = await session.execute(
        select(BroadcastDraft).where(BroadcastDraft.admin_telegram_id == admin_id)
    )
    return result.scalar_one_or_none()


async def delete_broadcast_draft(session: AsyncSession, admin_id: int) -> None:
    await session.execute(
        delete(BroadcastDraft).where(BroadcastDraft.admin_telegram_id == admin_id)
    )
    await session.commit()


async def record_star_payment(
    session: AsyncSession,
    *,
    user_telegram_id: int,
    charge_id: str,
    stars_amount: int,
    kind: str = "tip",
) -> StarPayment | None:
    payment = StarPayment(
        user_telegram_id=user_telegram_id,
        charge_id=charge_id,
        stars_amount=stars_amount,
        kind=kind,
    )
    session.add(payment)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return None
    await session.refresh(payment)
    return payment


async def get_star_tips_summary(session: AsyncSession) -> tuple[int, int]:
    """(count, total_stars) для kind=tip."""
    count_q = await session.execute(
        select(func.count())
        .select_from(StarPayment)
        .where(StarPayment.kind == "tip")
    )
    sum_q = await session.execute(
        select(func.coalesce(func.sum(StarPayment.stars_amount), 0))
        .select_from(StarPayment)
        .where(StarPayment.kind == "tip")
    )
    return int(count_q.scalar_one()), int(sum_q.scalar_one())


async def count_user_star_tips(session: AsyncSession, telegram_id: int) -> tuple[int, int]:
    count_q = await session.execute(
        select(func.count())
        .select_from(StarPayment)
        .where(
            StarPayment.user_telegram_id == telegram_id,
            StarPayment.kind == "tip",
        )
    )
    sum_q = await session.execute(
        select(func.coalesce(func.sum(StarPayment.stars_amount), 0))
        .select_from(StarPayment)
        .where(
            StarPayment.user_telegram_id == telegram_id,
            StarPayment.kind == "tip",
        )
    )
    return int(count_q.scalar_one()), int(sum_q.scalar_one())


async def count_user_done_reminders(session: AsyncSession, telegram_id: int) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(ReminderEvent)
        .where(
            ReminderEvent.user_telegram_id == telegram_id,
            ReminderEvent.event_kind == ReminderEventKind.DONE.value,
        )
    )
    return int(result.scalar_one())


async def set_user_tip_nudge_shown(
    session: AsyncSession,
    telegram_id: int,
    *,
    at: datetime | None = None,
) -> None:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is None:
        return
    user.tip_nudge_at = at or datetime.now(timezone.utc)
    await session.commit()


async def set_user_tip_nudge_dismissed(
    session: AsyncSession,
    telegram_id: int,
    *,
    at: datetime | None = None,
) -> None:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is None:
        return
    user.tip_nudge_dismissed_at = at or datetime.now(timezone.utc)
    await session.commit()


async def get_top_star_tippers(
    session: AsyncSession,
    *,
    days: int = 30,
    limit: int = 5,
) -> list[tuple[int, int, int]]:
    """(telegram_id, payment_count, total_stars) за период."""
    since = datetime.now(timezone.utc) - timedelta(days=max(1, days))
    rows = await session.execute(
        select(
            StarPayment.user_telegram_id,
            func.count(),
            func.sum(StarPayment.stars_amount),
        )
        .where(
            StarPayment.kind == "tip",
            StarPayment.created_at >= since,
        )
        .group_by(StarPayment.user_telegram_id)
        .order_by(func.sum(StarPayment.stars_amount).desc())
        .limit(limit)
    )
    return [(int(r[0]), int(r[1]), int(r[2])) for r in rows.all()]
