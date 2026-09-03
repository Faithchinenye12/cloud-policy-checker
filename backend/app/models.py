from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    requested_scans = relationship(
        "Scan",
        back_populates="requested_by_user",
    )
    assigned_remediations = relationship(
        "ComplianceResult",
        back_populates="assigned_to_user",
        foreign_keys="ComplianceResult.assigned_to_user_id",
    )


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resources = relationship(
        "Resource",
        back_populates="organization",
    )
    scans = relationship(
        "Scan",
        back_populates="organization",
    )


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    resource_type = Column(String, index=True)
    cloud_provider = Column(String, index=True)
    cloud_id = Column(String, unique=True)
    organization_id = Column(
        Integer,
        ForeignKey(
            "organizations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    region = Column(String, nullable=True)
    configuration = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False, default="active", index=True)
    first_discovered_at = Column(DateTime, default=datetime.utcnow)
    last_discovered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    organization = relationship(
        "Organization",
        back_populates="resources",
    )
    compliance_results = relationship(
        "ComplianceResult",
        back_populates="resource",
    )


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    severity = Column(String)
    cloud_provider = Column(String, nullable=False, default="aws", index=True)
    resource_type = Column(
        String,
        nullable=False,
        default="storage_bucket",
        index=True,
    )
    rule_type = Column(String, nullable=False, index=True)
    rule_config = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    compliance_results = relationship(
        "ComplianceResult",
        back_populates="policy",
    )


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey(
            "organizations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    requested_by_user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    cloud_provider = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=True, index=True)
    job_id = Column(String, nullable=True, unique=True, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    total_resources = Column(Integer, nullable=False, default=0)
    compliant_count = Column(Integer, nullable=False, default=0)
    non_compliant_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    organization = relationship(
        "Organization",
        back_populates="scans",
    )
    requested_by_user = relationship(
        "User",
        back_populates="requested_scans",
    )
    compliance_results = relationship(
        "ComplianceResult",
        back_populates="scan",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ComplianceResult(Base):
    __tablename__ = "compliance_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(
        Integer,
        ForeignKey(
            "scans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    resource_id = Column(
        Integer,
        ForeignKey(
            "resources.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    policy_id = Column(
        Integer,
        ForeignKey(
            "policies.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    compliant = Column(Boolean, nullable=False)
    details = Column(Text, nullable=False)
    remediation_status = Column(String, nullable=False, default="open", index=True)
    assigned_to_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    due_at = Column(DateTime, nullable=True)
    remediation_note = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship(
        "Scan",
        back_populates="compliance_results",
    )
    resource = relationship(
        "Resource",
        back_populates="compliance_results",
    )
    policy = relationship(
        "Policy",
        back_populates="compliance_results",
    )
    assigned_to_user = relationship(
        "User",
        back_populates="assigned_remediations",
        foreign_keys=[assigned_to_user_id],
    )
    remediation_events = relationship(
        "RemediationEvent",
        back_populates="compliance_result",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RemediationEvent(Base):
    __tablename__ = "remediation_events"

    id = Column(Integer, primary_key=True, index=True)
    compliance_result_id = Column(Integer, ForeignKey("compliance_results.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    previous_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    compliance_result = relationship("ComplianceResult", back_populates="remediation_events")
    actor_user = relationship("User", foreign_keys=[actor_user_id])
