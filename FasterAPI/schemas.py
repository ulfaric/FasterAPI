from pydantic import BaseModel, EmailStr

class UserInfo(BaseModel):
    """Schemas for User information."""
    username: str
    first_name: str
    last_name: str
    email: EmailStr

class UserAdmin(UserInfo):
    """Schemas for User information for administration."""
    password: str
    is_superuser: bool
    
class BearToken(BaseModel):
    """Schemas for Bear Token information."""
    token: str
    type: str = "Bearer"
