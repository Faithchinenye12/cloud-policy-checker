"""add compliance framework readiness"""
from alembic import op
import sqlalchemy as sa

revision = "b94d73f018a2"
down_revision = "862eb7ae319a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("compliance_frameworks", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("slug", sa.String(), nullable=False), sa.Column("name", sa.String(), nullable=False), sa.Column("version", sa.String(), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("source_url", sa.String(), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()), sa.UniqueConstraint("slug"))
    op.create_index("ix_compliance_frameworks_slug", "compliance_frameworks", ["slug"], unique=True)
    op.create_table("framework_controls", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("framework_id", sa.Integer(), sa.ForeignKey("compliance_frameworks.id", ondelete="CASCADE"), nullable=False), sa.Column("code", sa.String(), nullable=False), sa.Column("title", sa.String(), nullable=False), sa.Column("domain", sa.String(), nullable=False), sa.Column("guidance", sa.Text(), nullable=False), sa.UniqueConstraint("framework_id", "code", name="uq_framework_control_code"))
    op.create_index("ix_framework_controls_framework_id", "framework_controls", ["framework_id"])
    op.create_table("policy_framework_mappings", sa.Column("policy_id", sa.Integer(), sa.ForeignKey("policies.id", ondelete="CASCADE"), primary_key=True), sa.Column("control_id", sa.Integer(), sa.ForeignKey("framework_controls.id", ondelete="CASCADE"), primary_key=True), sa.Column("rationale", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))
    connection = op.get_bind()
    framework_rows = [
        ("cis-v8-1", "CIS Controls", "8.1", "Prioritized safeguards for reducing common cyber risk.", "https://www.cisecurity.org/controls/v8"),
        ("nist-csf-2", "NIST Cybersecurity Framework", "2.0", "Outcome-based guidance for governing and reducing cybersecurity risk.", "https://www.nist.gov/publications/nist-cybersecurity-framework-csf-20"),
        ("iso-27001-2022", "ISO/IEC 27001", "2022", "Information security management system readiness context.", "https://www.iso.org/standard/27001"),
        ("soc2-tsc", "SOC 2 Trust Services Criteria", "2017 / 2022 points of focus", "Security readiness context for service organization controls.", "https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022"),
    ]
    control_rows = [
        ("cis-v8-1", "CIS 3.3", "Data access controls", "Data Protection", "public_access_blocked"), ("cis-v8-1", "CIS 3.11", "Data-at-rest encryption", "Data Protection", "encryption_enabled"),
        ("nist-csf-2", "PR.AA-05", "Access permissions managed", "Protect", "public_access_blocked"), ("nist-csf-2", "PR.DS-01", "Data-at-rest protected", "Protect", "encryption_enabled"),
        ("iso-27001-2022", "A.5.15", "Access control readiness", "Organizational", "public_access_blocked"), ("iso-27001-2022", "A.8.24", "Cryptography readiness", "Technological", "encryption_enabled"),
        ("soc2-tsc", "CC6.1", "Logical access readiness", "Security", "public_access_blocked"), ("soc2-tsc", "CC6.7", "Protected information readiness", "Security", "encryption_enabled"),
    ]
    for slug, name, version, description, source_url in framework_rows:
        connection.execute(sa.text("INSERT INTO compliance_frameworks (slug,name,version,description,source_url) VALUES (:s,:n,:v,:d,:u)"), {"s":slug,"n":name,"v":version,"d":description,"u":source_url})
    for slug, code, title, domain, field in control_rows:
        control_id = connection.execute(sa.text("INSERT INTO framework_controls (framework_id,code,title,domain,guidance) SELECT id,:c,:t,:d,:g FROM compliance_frameworks WHERE slug=:s RETURNING id"), {"s":slug,"c":code,"t":title,"d":domain,"g":"CloudConform product-authored readiness crosswalk."}).scalar_one()
        connection.execute(sa.text("INSERT INTO policy_framework_mappings (policy_id,control_id,rationale) SELECT id,:cid,:r FROM policies WHERE rule_config->>'field'=:field ON CONFLICT DO NOTHING"), {"cid":control_id,"r":f"Policy evidence tests {field}.","field":field})


def downgrade() -> None:
    op.drop_table("policy_framework_mappings")
    op.drop_index("ix_framework_controls_framework_id", table_name="framework_controls")
    op.drop_table("framework_controls")
    op.drop_index("ix_compliance_frameworks_slug", table_name="compliance_frameworks")
    op.drop_table("compliance_frameworks")
