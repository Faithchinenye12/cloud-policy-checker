from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    resource_type = Column(String, index=True)
    cloud_provider = Column(String, index=True)
    cloud_id = Column(String, unique=True)
    organization_id = Column(Integer, index=True)
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


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    requested_by_user_id = Column(Integer, nullable=True, index=True)
    cloud_provider = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    total_resources = Column(Integer, nullable=False, default=0)
    compliant_count = Column(Integer, nullable=False, default=0)
    non_compliant_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class ComplianceResult(Base):
    __tablename__ = "compliance_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer)
    resource_id = Column(Integer)
    policy_id = Column(Integer)
    compliant = Column(Boolean)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)