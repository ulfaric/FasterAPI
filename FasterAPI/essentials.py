from __future__ import annotations

import os
import secrets
from typing import Dict

import yaml
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import logger

try:
    config: Dict = yaml.safe_load(open("./auth_config.yaml", "r"))
    logger.warning(
        "Configuration file auth_config.yaml not found. Default values will be used."
    )
except FileNotFoundError:
    config = {}

try:
    meta_config: Dict = yaml.safe_load(open("./meta_config.yaml", "r"))
    logger.warning(
        "Configuration file meta_config.yaml not found. Default values will be used."
    )
except FileNotFoundError:
    meta_config = {}


# set up database
SQLALCHEMY_DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL", config.get("SQLALCHEMY_DATABASE_URL", "sqlite:///dev.db")
)

if SQLALCHEMY_DATABASE_URL is None:
    raise Exception("SQLALCHEMY_DATABASE_URL is not set.")

Engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)


def get_db():
    global Engine
    global SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
