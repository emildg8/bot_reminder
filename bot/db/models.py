from datetime import datetime, time
from enum import Enum

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Time, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ReminderKind(str, Enum):
    ONCE = "once"
    INTERVAL = "interval"
    DAILY = "daily"
    WEEKLY = "weekly"


class ReminderEventKind(str, Enum):
    CREATED = "created"
    FIRED = "fired"
    SNOOZED = "snoozed"
    DONE = "done"
    DELETED = "deleted"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    timezone_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    snooze_presets: Mapped[str] = mapped_column(String(64), default="5,15,30,60,180,240")
    snooze_step: Mapped[int] = mapped_column(Integer, default=15)
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False)
    pro_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    onboarding_done: Mapped[bool] = mapped_column(Boolean, default=False)
    admin_tools_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reminders: Mapped[list["Reminder"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class ChatSettings(Base):
    __tablename__ = "chat_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    timezone_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    linked_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    created_by_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    mention_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    text: Mapped[str] = mapped_column(String(512))
    kind: Mapped[str] = mapped_column(String(16))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    interval_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    weekdays_mask: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_schedule_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="reminders")


class ReminderEvent(Base):
    __tablename__ = "reminder_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reminder_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    reminder_text: Mapped[str] = mapped_column(String(512))
    event_kind: Mapped[str] = mapped_column(String(16), index=True)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    extra: Mapped[str | None] = mapped_column(String(128), nullable=True)


class AdminAction(Base):
    __tablename__ = "admin_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    action: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class BroadcastDraft(Base):
    __tablename__ = "broadcast_drafts"

    admin_telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    text: Mapped[str] = mapped_column(String(4096))
    filter: Mapped[str] = mapped_column(String(16), default="all")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StarPayment(Base):
    __tablename__ = "star_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    charge_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    stars_amount: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
