import os
import secrets
from datetime import datetime
from typing import Dict, List

import yaml
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from FasterAPI import Module, core

user_module = Module(module_name="user")
core.modules.append(user_module)

try:
    config: Dict = yaml.safe_load(open("config.yaml", "r")) or {}
except FileNotFoundError:
    config = {}

SECRET_KEY = os.getenv("SECRET_KEY", config.get("SECRET_KEY", secrets.token_hex(32)))
ALGORITHM = os.getenv("ALGORITHM", config.get("ALGORITHM", "HS256"))
TOKEN_URL = os.getenv("TOKEN_URL", config.get("TOKEN_URL", "login"))
TOKEN_EXPIRATION_TIME = int(
    os.getenv(
        "TOKEN_EXPIRATION_TIME",
        config.get("TOKEN_EXPIRATION_TIME", 15),
    )
)
ALLOW_MULTI_SESSIONS = os.getenv(
    "ALLOW_MULTI_SESSIONS", config.get("ALLOW_MULTI_SESSIONS", True)
)
ALLOW_SELF_REGISTRATION = os.getenv(
    "ALLOW_SELF_REGISTRATION", config.get("ALLOW_SELF_REGISTRATION", False)
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

class User(user_module.base):
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


class UserPrivilege(user_module.base):
    """User role model"""

    __tablename__ = "user_privileges"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    privilege: Mapped[str]
    user: Mapped["User"] = relationship("User", back_populates="privileges")


class ActiveSession(user_module.base):
    """Active session model""" ""

    __tablename__ = "active_sessions"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        ForeignKey("users.username"), index=True, unique=True
    )
    client: Mapped[str]
    exp: Mapped[datetime]
    user: Mapped["User"] = relationship("User", back_populates="session")


class BlacklistedToken(user_module.base):
    """Blacklisted token model""" ""

    __tablename__ = "blacklisted_tokens"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column(unique=True, index=True)
    exp: Mapped[datetime]