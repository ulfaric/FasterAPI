from sqlalchemy import Column, Integer, String, DateTime, Boolean
from . import Base

class User(Base):
    """User model"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    role = Column(String)
    hashed_password = Column(String)
    is_superuser = Column(Boolean, default=False)   

class BlacklistedToken(Base):
    """Blacklisted token model"""""
    __tablename__ = "blacklisted_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    exp = Column(DateTime)
