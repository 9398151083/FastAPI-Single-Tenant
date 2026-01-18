"""add tasks table
Revision ID: b7c2365f6c25
Revises: d240655da725
Create Date: 2026-01-18 12:36:37.144181
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b7c2365f6c25"
down_revision = "d240655da725"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ✅ STEP 1: Add created_by as NULLABLE first (no error)
    op.add_column(
        "tasks", sa.Column("created_by", sa.UUID(as_uuid=False), nullable=True)
    )

    # ✅ STEP 2: Fill ALL existing rows with default creator UUID
    op.execute("UPDATE tasks SET created_by = '0fa23517-6b1d-449b-87bc-28f69598f75c'")

    # ✅ STEP 3: NOW make created_by NOT NULL (safe)
    op.alter_column("tasks", "created_by", nullable=False)

    # ✅ STEP 4: Add created_at column
    op.add_column("tasks", sa.Column("created_at", sa.DateTime(), nullable=True))

    # ✅ STEP 5: Rest of your column changes (safe)
    op.alter_column(
        "tasks",
        "status",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.String(length=20),
        nullable=True,
    )
    op.alter_column(
        "tasks",
        "priority",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.String(length=20),
        nullable=True,
    )
    op.alter_column(
        "tasks",
        "due_date",
        existing_type=sa.DATE(),
        type_=sa.DateTime(),
        existing_nullable=True,
    )
    op.drop_column("tasks", "parent_id")


def downgrade() -> None:
    # Reverse operations
    op.add_column(
        "tasks", sa.Column("parent_id", sa.UUID(), autoincrement=False, nullable=True)
    )
    op.alter_column(
        "tasks",
        "due_date",
        existing_type=sa.DateTime(),
        type_=sa.DATE(),
        existing_nullable=True,
    )
    op.alter_column(
        "tasks",
        "priority",
        existing_type=sa.String(length=20),
        type_=sa.VARCHAR(length=50),
        nullable=False,
    )
    op.alter_column(
        "tasks",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.VARCHAR(length=50),
        nullable=False,
    )
    op.drop_column("tasks", "created_at")
    op.drop_column("tasks", "created_by")
