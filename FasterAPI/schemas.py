from pydantic import BaseModel, EmailStr
from typing import List


class Privilege(BaseModel):
    """Schemas for User Priviliege information."""

    privilege: str


class UserInfo(BaseModel):
    """Schemas for User information."""

    username: str
    first_name: str
    last_name: str
    email: EmailStr
    privileges: List[Privilege]
    is_superuser: bool


class UserCreate(UserInfo):
    """Schemas for User information for administration."""

    password: str


class UserUpdate(BaseModel):
    """Schemas for User information for administration."""

    first_name: str
    last_name: str
    email: EmailStr
    password: str


class BearToken(BaseModel):
    """Schemas for Bear Token information."""

    token: str
    type: str = "Bearer"
