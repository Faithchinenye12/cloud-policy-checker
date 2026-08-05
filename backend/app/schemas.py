from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
    name: str
    description: str
    severity: str


class Policy(PolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int