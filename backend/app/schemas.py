from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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
    name: str
    resource_type: str
    cloud_provider: str


class Resource(ResourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PolicyBase(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=10, max_length=1000)
    severity: Literal["low", "medium", "high", "critical"]
    cloud_provider: Literal["aws", "azure", "gcp"]
    resource_type: str = Field(min_length=3, max_length=100)
    rule_type: Literal["boolean_property_equals", "field_must_exist"]
    rule_config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_rule_config(self) -> "PolicyBase":
        field_name = self.rule_config.get("field")
        if not isinstance(field_name, str) or not field_name.strip():
            raise ValueError("rule_config must include a non-empty 'field' name.")

        if self.rule_type == "boolean_property_equals":
            expected_value = self.rule_config.get("expected_value")
            if not isinstance(expected_value, bool):
                raise ValueError(
                    "boolean_property_equals requires a boolean 'expected_value'."
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
    cloud_provider: Literal["aws", "azure", "gcp"]
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