"""widen metrics.value_str so it can hold rationale text

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE metrics ALTER COLUMN value_str TYPE TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE metrics ALTER COLUMN value_str TYPE VARCHAR(64)")
