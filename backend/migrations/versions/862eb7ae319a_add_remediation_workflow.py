"""add remediation workflow

Revision ID: 862eb7ae319a
Revises: 1799fecac34b
Create Date: 2026-09-03 07:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "862eb7ae319a"
down_revision: Union[str, Sequence[str], None] = "1799fecac34b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("compliance_results", sa.Column("remediation_status", sa.String(), nullable=False, server_default="open"))
    op.add_column("compliance_results", sa.Column("assigned_to_user_id", sa.Integer(), nullable=True))
    op.add_column("compliance_results", sa.Column("due_at", sa.DateTime(), nullable=True))
    op.add_column("compliance_results", sa.Column("remediation_note", sa.Text(), nullable=True))
    op.add_column("compliance_results", sa.Column("resolved_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_compliance_results_remediation_status"), "compliance_results", ["remediation_status"])
    op.create_index(op.f("ix_compliance_results_assigned_to_user_id"), "compliance_results", ["assigned_to_user_id"])
    op.create_foreign_key("fk_compliance_results_assigned_user", "compliance_results", "users", ["assigned_to_user_id"], ["id"], ondelete="SET NULL")
    op.create_table(
        "remediation_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("compliance_result_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("previous_status", sa.String(), nullable=False),
        sa.Column("new_status", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["compliance_result_id"], ["compliance_results.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_remediation_events_id"), "remediation_events", ["id"])
    op.create_index(op.f("ix_remediation_events_compliance_result_id"), "remediation_events", ["compliance_result_id"])
    op.create_index(op.f("ix_remediation_events_actor_user_id"), "remediation_events", ["actor_user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_remediation_events_actor_user_id"), table_name="remediation_events")
    op.drop_index(op.f("ix_remediation_events_compliance_result_id"), table_name="remediation_events")
    op.drop_index(op.f("ix_remediation_events_id"), table_name="remediation_events")
    op.drop_table("remediation_events")
    op.drop_constraint("fk_compliance_results_assigned_user", "compliance_results", type_="foreignkey")
    op.drop_index(op.f("ix_compliance_results_assigned_to_user_id"), table_name="compliance_results")
    op.drop_index(op.f("ix_compliance_results_remediation_status"), table_name="compliance_results")
    op.drop_column("compliance_results", "resolved_at")
    op.drop_column("compliance_results", "remediation_note")
    op.drop_column("compliance_results", "due_at")
    op.drop_column("compliance_results", "assigned_to_user_id")
    op.drop_column("compliance_results", "remediation_status")
