from typing import List
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """User model"""

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[str]
    hashed_password: Mapped[str]
    is_superuser: Mapped[bool]
    privileges: Mapped[List["UserPrivilege"]] = relationship(
        back_populates="user", cascade="all,delete"
    )
    session: Mapped["ActiveSession"] = relationship(
        back_populates="user", cascade="all,delete"
    )


class UserPrivilege(Base):
    """User role model"""

    __tablename__ = "user_privileges"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    privilege: Mapped[str]
    user: Mapped["User"] = relationship("User", back_populates="privileges")


class ActiveSession(Base):
    """Active session model""" ""

    __tablename__ = "active_sessions"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username"), index=True, unique=True
    )
    client: Mapped[str]
    exp: Mapped[datetime]
    user: Mapped["User"] = relationship("User", back_populates="session")


class BlacklistedToken(Base):
    """Blacklisted token model""" ""

    __tablename__ = "blacklisted_tokens"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column(unique=True, index=True)
    exp: Mapped[datetime]
