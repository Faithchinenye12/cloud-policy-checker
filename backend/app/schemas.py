from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


CloudProvider = Literal["aws", "azure", "gcp"]
ResourceStatus = Literal["active", "inactive"]
ScanStatus = Literal[
    "pending",
    "queued",
    "running",
    "completed",
    "failed",
]
RemediationStatus = Literal["open", "in_progress", "resolved", "risk_accepted"]


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class ResourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    resource_type: str = Field(min_length=3, max_length=100)
    cloud_provider: CloudProvider
    cloud_id: str = Field(min_length=1, max_length=500)
    organization_id: Optional[int] = Field(default=None, ge=1)
    region: Optional[str] = Field(default=None, max_length=100)
    configuration: dict[str, Any] = Field(default_factory=dict)
    status: ResourceStatus = "active"


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    region: Optional[str] = Field(default=None, max_length=100)
    configuration: Optional[dict[str, Any]] = None
    status: Optional[ResourceStatus] = None


class Resource(ResourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_discovered_at: datetime
    last_discovered_at: datetime
    created_at: datetime
    updated_at: datetime


class PolicyBase(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=1000)
    severity: Literal["low", "medium", "high", "critical"]
    cloud_provider: CloudProvider
    resource_type: str = Field(min_length=3, max_length=100)
    rule_type: Literal["boolean_property_equals", "field_must_exist"]
    rule_config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_rule_config(self) -> "PolicyBase":
        field_name = self.rule_config.get("field")
        if not isinstance(field_name, str) or not field_name.strip():
            raise ValueError(
                "rule_config must include a non-empty 'field' name."
            )

        if self.rule_type == "boolean_property_equals":
            expected_value = self.rule_config.get("expected_value")
            if not isinstance(expected_value, bool):
                raise ValueError(
                    "boolean_property_equals requires a boolean "
                    "'expected_value'."
                )

        return self


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(PolicyBase):
    is_active: bool = True


class Policy(PolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class PolicyEvaluationRequest(BaseModel):
    resource_name: str = Field(min_length=1, max_length=200)
    cloud_provider: CloudProvider
    resource_type: str = Field(min_length=3, max_length=100)
    configuration: dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResult(BaseModel):
    policy_id: int
    policy_name: str
    severity: str
    compliant: bool
    details: str


class PolicyEvaluationResponse(BaseModel):
    resource_name: str
    checked_policy_count: int
    results: list[PolicyEvaluationResult]


class ScanCreate(BaseModel):
    organization_id: Optional[int] = Field(default=None, ge=1)
    cloud_provider: CloudProvider
    resource_type: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=100,
    )


class Scan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: Optional[int]
    requested_by_user_id: Optional[int]
    cloud_provider: CloudProvider
    resource_type: Optional[str]
    job_id: Optional[str]
    status: ScanStatus
    total_resources: int
    compliant_count: int
    non_compliant_count: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class ComplianceResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int
    resource_id: int
    policy_id: int
    compliant: bool
    details: str
    remediation_status: RemediationStatus = "open"
    assigned_to_user_id: Optional[int] = None
    due_at: Optional[datetime] = None
    remediation_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


class RemediationUpdate(BaseModel):
    status: RemediationStatus
    assigned_to_user_id: Optional[int] = Field(default=None, ge=1)
    due_at: Optional[datetime] = None
    note: Optional[str] = Field(default=None, max_length=2000)


class RemediationEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    compliance_result_id: int
    actor_user_id: Optional[int]
    previous_status: RemediationStatus
    new_status: RemediationStatus
    note: Optional[str]
    created_at: datetime


class RemediationRecord(ComplianceResult):
    remediation_events: list[RemediationEvent] = Field(default_factory=list)


class IntelligenceNode(BaseModel):
    id: str
    kind: Literal["resource", "policy", "scan", "finding"]
    label: str
    status: str
    severity: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntelligenceEdge(BaseModel):
    source: str
    target: str
    relationship: Literal[
        "evaluated",
        "checked_by",
        "produced",
        "affects",
        "violates",
    ]


class IntelligenceAction(BaseModel):
    finding_id: int
    resource_id: int
    policy_id: int
    severity: str
    title: str
    recommendation: str


class IntelligenceSummary(BaseModel):
    resources: int
    policies: int
    scans: int
    open_findings: int
    risk_score: int = Field(ge=0, le=100)


class IntelligenceGraph(BaseModel):
    summary: IntelligenceSummary
    nodes: list[IntelligenceNode]
    edges: list[IntelligenceEdge]
    priority_actions: list[IntelligenceAction]


class ControlReadiness(BaseModel):
    code: str
    title: str
    domain: str
    status: Literal["passed", "failed", "accepted", "not_assessed"]
    mapped_policies: int
    evidence_count: int


class FrameworkReadiness(BaseModel):
    slug: str
    name: str
    version: str
    description: str
    source_url: str
    readiness_percent: int = Field(ge=0, le=100)
    passed: int
    failed: int
    accepted: int
    not_assessed: int
    controls: list[ControlReadiness]


class ComplianceReadinessResponse(BaseModel):
    disclaimer: str
    frameworks: list[FrameworkReadiness]
