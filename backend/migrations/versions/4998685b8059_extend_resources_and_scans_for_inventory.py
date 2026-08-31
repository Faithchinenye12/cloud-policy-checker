"""extend resources and scans for inventory

Revision ID: 4998685b8059
Revises: 7fdfeef69e2
Create Date: 2026-08-31 03:11:19.737655

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4998685b8059"
down_revision: Union[str, Sequence[str], None] = "7fdfeef69e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add cloud-resource inventory and scan-lifecycle fields."""
    op.add_column(
        "resources",
        sa.Column("region", sa.String(), nullable=True),
    )
    op.add_column(
        "resources",
        sa.Column(
            "configuration",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )
    op.add_column(
        "resources",
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "resources",
        sa.Column(
            "first_discovered_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        "resources",
        sa.Column(
            "last_discovered_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        "resources",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_resources_cloud_provider"),
        "resources",
        ["cloud_provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resources_organization_id"),
        "resources",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resources_resource_type"),
        "resources",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resources_status"),
        "resources",
        ["status"],
        unique=False,
    )

    op.alter_column(
        "resources",
        "configuration",
        server_default=None,
    )
    op.alter_column(
        "resources",
        "status",
        server_default=None,
    )

    op.add_column(
        "scans",
        sa.Column(
            "requested_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "scans",
        sa.Column(
            "cloud_provider",
            sa.String(),
            nullable=False,
            server_default="aws",
        ),
    )
    op.add_column(
        "scans",
        sa.Column(
            "resource_type",
            sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        "scans",
        sa.Column(
            "total_resources",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "scans",
        sa.Column(
            "compliant_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "scans",
        sa.Column(
            "non_compliant_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "scans",
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "scans",
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            "UPDATE scans SET status = 'pending' "
            "WHERE status IS NULL"
        )
    )
    op.alter_column(
        "scans",
        "status",
        existing_type=sa.String(),
        nullable=False,
    )

    op.create_index(
        op.f("ix_scans_cloud_provider"),
        "scans",
        ["cloud_provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scans_organization_id"),
        "scans",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scans_requested_by_user_id"),
        "scans",
        ["requested_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scans_resource_type"),
        "scans",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scans_status"),
        "scans",
        ["status"],
        unique=False,
    )

    op.alter_column(
        "scans",
        "cloud_provider",
        server_default=None,
    )
    op.alter_column(
        "scans",
        "total_resources",
        server_default=None,
    )
    op.alter_column(
        "scans",
        "compliant_count",
        server_default=None,
    )
    op.alter_column(
        "scans",
        "non_compliant_count",
        server_default=None,
    )


def downgrade() -> None:
    """Remove cloud-resource inventory and scan-lifecycle fields."""
    op.drop_index(
        op.f("ix_scans_status"),
        table_name="scans",
    )
    op.drop_index(
        op.f("ix_scans_resource_type"),
        table_name="scans",
    )
    op.drop_index(
        op.f("ix_scans_requested_by_user_id"),
        table_name="scans",
    )
    op.drop_index(
        op.f("ix_scans_organization_id"),
        table_name="scans",
    )
    op.drop_index(
        op.f("ix_scans_cloud_provider"),
        table_name="scans",
    )

    op.alter_column(
        "scans",
        "status",
        existing_type=sa.String(),
        nullable=True,
    )

    op.drop_column("scans", "started_at")
    op.drop_column("scans", "error_message")
    op.drop_column("scans", "non_compliant_count")
    op.drop_column("scans", "compliant_count")
    op.drop_column("scans", "total_resources")
    op.drop_column("scans", "resource_type")
    op.drop_column("scans", "cloud_provider")
    op.drop_column("scans", "requested_by_user_id")

    op.drop_index(
        op.f("ix_resources_status"),
        table_name="resources",
    )
    op.drop_index(
        op.f("ix_resources_resource_type"),
        table_name="resources",
    )
    op.drop_index(
        op.f("ix_resources_organization_id"),
        table_name="resources",
    )
    op.drop_index(
        op.f("ix_resources_cloud_provider"),
        table_name="resources",
    )

    op.drop_column("resources", "updated_at")
    op.drop_column("resources", "last_discovered_at")
    op.drop_column("resources", "first_discovered_at")
    op.drop_column("resources", "status")
    op.drop_column("resources", "configuration")
    op.drop_column("resources", "region")