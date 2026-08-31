"""add relational integrity for scan results

Revision ID: adcfbbd20c35
Revises: 4998685b8059
Create Date: 2026-08-31 03:50:21.339939

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "adcfbbd20c35"
down_revision: Union[str, Sequence[str], None] = "4998685b8059"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add required result fields and explicit foreign keys."""
    op.alter_column(
        "compliance_results",
        "scan_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "compliance_results",
        "resource_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "compliance_results",
        "policy_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "compliance_results",
        "compliant",
        existing_type=sa.Boolean(),
        nullable=False,
    )
    op.alter_column(
        "compliance_results",
        "details",
        existing_type=sa.Text(),
        nullable=False,
    )

    op.create_foreign_key(
        "fk_compliance_results_scan_id_scans",
        "compliance_results",
        "scans",
        ["scan_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_compliance_results_resource_id_resources",
        "compliance_results",
        "resources",
        ["resource_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_compliance_results_policy_id_policies",
        "compliance_results",
        "policies",
        ["policy_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_resources_organization_id_organizations",
        "resources",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_scans_requested_by_user_id_users",
        "scans",
        "users",
        ["requested_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_scans_organization_id_organizations",
        "scans",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove explicit foreign keys and restore nullable result fields."""
    op.drop_constraint(
        "fk_scans_organization_id_organizations",
        "scans",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_scans_requested_by_user_id_users",
        "scans",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_resources_organization_id_organizations",
        "resources",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_compliance_results_policy_id_policies",
        "compliance_results",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_compliance_results_resource_id_resources",
        "compliance_results",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_compliance_results_scan_id_scans",
        "compliance_results",
        type_="foreignkey",
    )

    op.alter_column(
        "compliance_results",
        "details",
        existing_type=sa.Text(),
        nullable=True,
    )
    op.alter_column(
        "compliance_results",
        "compliant",
        existing_type=sa.Boolean(),
        nullable=True,
    )
    op.alter_column(
        "compliance_results",
        "policy_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "compliance_results",
        "resource_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "compliance_results",
        "scan_id",
        existing_type=sa.Integer(),
        nullable=True,
    )