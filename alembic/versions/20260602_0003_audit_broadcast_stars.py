"""admin audit, broadcast drafts, star payments, pro_expires_at

Revision ID: 20260602_0003
Revises: 20260601_0002
Create Date: 2026-06-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260602_0003"
down_revision: Union[str, None] = "20260601_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("pro_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "admin_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_actions_admin_telegram_id", "admin_actions", ["admin_telegram_id"])
    op.create_index("ix_admin_actions_created_at", "admin_actions", ["created_at"])
    op.create_table(
        "broadcast_drafts",
        sa.Column("admin_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.String(length=4096), nullable=False),
        sa.Column("filter", sa.String(length=16), nullable=False, server_default="all"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("admin_telegram_id"),
    )
    op.create_table(
        "star_payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("charge_id", sa.String(length=128), nullable=False),
        sa.Column("stars_amount", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("charge_id"),
    )
    op.create_index("ix_star_payments_user_telegram_id", "star_payments", ["user_telegram_id"])
    op.create_index("ix_star_payments_charge_id", "star_payments", ["charge_id"])


def downgrade() -> None:
    op.drop_index("ix_star_payments_charge_id", table_name="star_payments")
    op.drop_index("ix_star_payments_user_telegram_id", table_name="star_payments")
    op.drop_table("star_payments")
    op.drop_table("broadcast_drafts")
    op.drop_index("ix_admin_actions_created_at", table_name="admin_actions")
    op.drop_index("ix_admin_actions_admin_telegram_id", table_name="admin_actions")
    op.drop_table("admin_actions")
    op.drop_column("users", "pro_expires_at")
