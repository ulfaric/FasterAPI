from pydantic import BaseModel, EmailStr


class UserInfo(BaseModel):
    """Schemas for User information."""

    username: str
    first_name: str
    last_name: str
    email: EmailStr


class UserCreate(UserInfo):
    """Schemas for User information for administration."""

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
