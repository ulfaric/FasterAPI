from typing import List

from pydantic import BaseModel, EmailStr


class Privilege(BaseModel):
    """Schemas for User Priviliege information."""

    privilege: str


class UserRead(BaseModel):
    """Schemas for read User information."""

    username: str
    first_name: str
    last_name: str
    email: EmailStr
    privileges: List[Privilege]
    is_superuser: bool


class UserCreate(BaseModel):
    """Schemas for create new user."""

    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    is_superuser: bool


class UserUpdate(BaseModel):
    """Schemas for update user information."""

    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserDelete(BaseModel):
    """Schemas for delete user."""

    username: str


class BearToken(BaseModel):
    """Schemas for Bear Token information."""

    token: str
    type: str = "Bearer"
