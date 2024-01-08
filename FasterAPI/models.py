from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from . import Base


class User(Base):
    """User model"""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    hashed_password = Column(String)
    is_superuser = Column(Boolean, default=False)
    privileges = relationship(
        "UserPrivilege", back_populates="user", cascade="all,delete"
    )


class UserPrivilege(Base):
    """User role model"""

    __tablename__ = "user_privileges"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    privilege = Column(String)
    user = relationship("User", back_populates="privileges")


class BlacklistedToken(Base):
    """Blacklisted token model""" ""

    __tablename__ = "blacklisted_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    exp = Column(DateTime)
