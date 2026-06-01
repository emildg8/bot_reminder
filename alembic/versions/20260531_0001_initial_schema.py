"""initial schema

Revision ID: 20260531_0001
Revises:
Create Date: 2026-05-31

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260531_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("timezone_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "snooze_presets",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'5,15,30,60,180,240'"),
        ),
        sa.Column("snooze_step", sa.Integer(), nullable=False, server_default=sa.text("15")),
        sa.Column("is_pro", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("onboarding_done", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=True)

    op.create_table(
        "chat_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("timezone_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("linked_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("is_paused", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_settings_chat_id"), "chat_settings", ["chat_id"], unique=True)

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("created_by_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("mention_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("text", sa.String(length=512), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interval_seconds", sa.Integer(), nullable=True),
        sa.Column("daily_time", sa.Time(), nullable=True),
        sa.Column("weekdays_mask", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("telegram_schedule_message_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reminders_chat_id"), "reminders", ["chat_id"], unique=False)
    op.create_index(op.f("ix_reminders_created_by_telegram_id"), "reminders", ["created_by_telegram_id"], unique=False)
    op.create_index(op.f("ix_reminders_user_id"), "reminders", ["user_id"], unique=False)

    op.create_table(
        "reminder_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reminder_id", sa.Integer(), nullable=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("reminder_text", sa.String(length=512), nullable=False),
        sa.Column("event_kind", sa.String(length=16), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("extra", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reminder_events_chat_id"), "reminder_events", ["chat_id"], unique=False)
    op.create_index(op.f("ix_reminder_events_event_at"), "reminder_events", ["event_at"], unique=False)
    op.create_index(op.f("ix_reminder_events_event_kind"), "reminder_events", ["event_kind"], unique=False)
    op.create_index(op.f("ix_reminder_events_reminder_id"), "reminder_events", ["reminder_id"], unique=False)
    op.create_index(op.f("ix_reminder_events_user_telegram_id"), "reminder_events", ["user_telegram_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reminder_events_user_telegram_id"), table_name="reminder_events")
    op.drop_index(op.f("ix_reminder_events_reminder_id"), table_name="reminder_events")
    op.drop_index(op.f("ix_reminder_events_event_kind"), table_name="reminder_events")
    op.drop_index(op.f("ix_reminder_events_event_at"), table_name="reminder_events")
    op.drop_index(op.f("ix_reminder_events_chat_id"), table_name="reminder_events")
    op.drop_table("reminder_events")
    op.drop_index(op.f("ix_reminders_user_id"), table_name="reminders")
    op.drop_index(op.f("ix_reminders_created_by_telegram_id"), table_name="reminders")
    op.drop_index(op.f("ix_reminders_chat_id"), table_name="reminders")
    op.drop_table("reminders")
    op.drop_index(op.f("ix_chat_settings_chat_id"), table_name="chat_settings")
    op.drop_table("chat_settings")
    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
