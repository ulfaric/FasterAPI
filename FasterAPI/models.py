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
    session = relationship("ActiveSession", back_populates="user", cascade="all,delete", uselist=False)


class UserPrivilege(Base):
    """User role model"""

    __tablename__ = "user_privileges"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    scope = Column(String)
    user = relationship("User", back_populates="privileges")


class ActiveSession(Base):
    """Active session model""" ""

    __tablename__ = "active_sessions"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), index=True)
    client = Column(String, unique=True, index=True)
    exp = Column(DateTime)
    user = relationship("User", back_populates="session")


class BlacklistedToken(Base):
    """Blacklisted token model""" ""

    __tablename__ = "blacklisted_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    exp = Column(DateTime)
