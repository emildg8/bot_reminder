"""star_payments.kind for tips vs legacy pro

Revision ID: 20260603_0004
Revises: 20260602_0003
Create Date: 2026-06-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0004"
down_revision: Union[str, None] = "20260602_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "star_payments",
        sa.Column("kind", sa.String(length=16), nullable=False, server_default="tip"),
    )


def downgrade() -> None:
    op.drop_column("star_payments", "kind")
