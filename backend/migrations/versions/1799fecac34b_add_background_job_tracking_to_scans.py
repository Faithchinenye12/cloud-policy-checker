"""add background job tracking to scans

Revision ID: 1799fecac34b
Revises: adcfbbd20c35
Create Date: 2026-08-31 04:10:00.765564

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1799fecac34b"
down_revision: Union[str, Sequence[str], None] = "adcfbbd20c35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add a unique Celery job identifier to scans."""
    op.add_column(
        "scans",
        sa.Column(
            "job_id",
            sa.String(),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_scans_job_id"),
        "scans",
        ["job_id"],
        unique=True,
    )


def downgrade() -> None:
    """Remove Celery job tracking from scans."""
    op.drop_index(
        op.f("ix_scans_job_id"),
        table_name="scans",
    )
    op.drop_column(
        "scans",
        "job_id",
    )