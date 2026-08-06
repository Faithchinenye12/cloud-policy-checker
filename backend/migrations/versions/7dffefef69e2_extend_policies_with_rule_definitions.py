"""extend policies with rule definitions

Revision ID: 7fdfeef69e2
Revises: 3d0ab99bdf1c
Create Date: 2026-08-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7fdfeef69e2"
down_revision: Union[str, Sequence[str], None] = "3d0ab99bdf1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add rule-definition fields needed by the policy engine."""
    op.add_column(
        "policies",
        sa.Column(
            "cloud_provider",
            sa.String(),
            nullable=False,
            server_default="aws",
        ),
    )
    op.add_column(
        "policies",
        sa.Column(
            "resource_type",
            sa.String(),
            nullable=False,
            server_default="storage_bucket",
        ),
    )
    op.add_column(
        "policies",
        sa.Column(
            "rule_type",
            sa.String(),
            nullable=False,
            server_default="boolean_property_equals",
        ),
    )
    op.add_column(
        "policies",
        sa.Column(
            "rule_config",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )
    op.add_column(
        "policies",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.create_index(
        op.f("ix_policies_cloud_provider"),
        "policies",
        ["cloud_provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_policies_resource_type"),
        "policies",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_policies_rule_type"),
        "policies",
        ["rule_type"],
        unique=False,
    )

    op.alter_column("policies", "cloud_provider", server_default=None)
    op.alter_column("policies", "resource_type", server_default=None)
    op.alter_column("policies", "rule_type", server_default=None)
    op.alter_column("policies", "rule_config", server_default=None)
    op.alter_column("policies", "is_active", server_default=None)


def downgrade() -> None:
    """Remove the policy rule-definition fields."""
    op.drop_index(op.f("ix_policies_rule_type"), table_name="policies")
    op.drop_index(op.f("ix_policies_resource_type"), table_name="policies")
    op.drop_index(op.f("ix_policies_cloud_provider"), table_name="policies")
    op.drop_column("policies", "is_active")
    op.drop_column("policies", "rule_config")
    op.drop_column("policies", "rule_type")
    op.drop_column("policies", "resource_type")
    op.drop_column("policies", "cloud_provider")
