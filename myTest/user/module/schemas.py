from typing import List

from pydantic import BaseModel, EmailStr


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


class UserCreate(BaseModel):
    """Schemas for User registration under superuser."""

    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    is_superuser: bool


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