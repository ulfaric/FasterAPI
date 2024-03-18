from __future__ import annotations

import asyncio
import logging
import os
import pickle
import secrets
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

import colorlog
import yaml
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, BlacklistedToken, User
from .schemas import UserCreate

# set up logging
logger = logging.getLogger("FasterAPI")
stream_handler = logging.StreamHandler()

# Define log colors
cformat = "%(log_color)s%(levelname)s:\t%(message)s"
colors = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red,bg_white",
}

stream_formatter = colorlog.ColoredFormatter(cformat, log_colors=colors)
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


# Load configuration
def load_auth_config(file_path):
    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warn(
            f"Authentication Configuration file {file_path} not found. Default configuration will be used."
        )
        return {}
    except PermissionError:
        logger.warn(
            f"No permission to read the file {file_path}. Default configuration will be used."
        )
        return {}
    return config


def load_meta_config(file_path):
    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warn(
            f"Meta Configuration file {file_path} not found. Default configuration will be used."
        )
        return {}
    except PermissionError:
        logger.warn(
            f"No permission to read the file {file_path}. Default configuration will be used."
        )
        return {}
    return config


config = load_auth_config("auth_config.yaml")
meta_config = load_meta_config("meta_config.yaml")

if config is None:
    raise Exception("Configuration file can not be loaded.")

# set up database
SQLALCHEMY_DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL", config.get("SQLALCHEMY_DATABASE_URL")
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


# define neccessary functions
async def _clean_up_expired_tokens():
    """A async task to cleanup expired tokens from the database. Maintains a optimal performance."""
    while True:
        db = next(get_db())
        db.query(BlacklistedToken).filter(
            BlacklistedToken.exp < datetime.now()
        ).delete()
        db.commit()
        db.close()
        logger.debug("Expired tokens cleaned up.")
        await asyncio.sleep(TOKEN_EXPIRATION_TIME * 60)


def _register_user(user: UserCreate):
    """Registers a new user."""
    db = next(get_db())
    extsing_user = db.query(User).filter(User.username == user.username).first()
    if extsing_user:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="User already exists.",
        )
    new_user = User(
        username=user.username,
        hashed_password=pwd_context.hash(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        is_superuser=user.is_superuser,
    )
    db.add(new_user)
    db.commit()
    logger.debug(f"User {user.username} registered.")
    return user


# define lifespan
@asynccontextmanager
async def _lifespan(app: FastAPI):
    Base.metadata.create_all(bind=Engine)
    logger.debug("Database initialized.")
    db = next(get_db())
    try:
        with open(".superuser", "rb") as f:
            superusers: List[User] = pickle.load(f)
            for superuser in superusers:
                try:
                    _register_user(superuser)
                except HTTPException:
                    logger.debug(f"Superuser {superuser.username} already exists.")
        os.remove(".superuser")
    except FileNotFoundError:
        pass

    try:
        with open(".users", "rb") as f:
            users: List[User] = pickle.load(f)
            for user in users:
                try:
                    _register_user(user)
                except HTTPException:
                    logger.debug(f"User {user.username} already exists.")
        os.remove(".users")
    except FileNotFoundError:
        pass
    logger.debug("Superusers and users registered.")
    expired_token_cleaner = asyncio.create_task(_clean_up_expired_tokens())
    yield
    expired_token_cleaner.cancel()


# define app
app = FastAPI(
    debug=bool(os.getenv("DEBUG", meta_config.get("DEBUG", False))),
    title=os.getenv("TITLE", meta_config.get("TITLE", "FasterAPI")),
    description=os.getenv(
        "DESCRIPTION",
        meta_config.get(
            "DESCRIPTION",
            "A FastAPI starter template with prebuilt JWT auth system.",
        ),
    ),
    version=os.getenv("VERSION", meta_config.get("VERSION", "0.0.1")),
    openapi_url=os.getenv(
        "OPENAPI_URL", meta_config.get("OPENAPI_URL", "/openapi.json")
    ),
    docs_url=os.getenv("DOCS_URL", meta_config.get("DOCS_URL", "/docs")),
    redoc_url=os.getenv("REDOC_URL", meta_config.get("REDOC_URL", "/redoc")),
    terms_of_service=os.getenv(
        "TERMS_OF_SERVICE", meta_config.get("TERMS_OF_SERVICE", None)
    ),
    contact=os.getenv("CONTACT", meta_config.get("CONTACT", None)),  # type: ignore
    summary=os.getenv("SUMMARY", meta_config.get("SUMMARY", None)),
    lifespan=_lifespan,
)

allow_origins = os.getenv("ALLOWED_ORIGINS", config.get("ALLOWED_ORIGINS", ["*"]))
allow_credentials = os.getenv(
    "ALLOW_CREDENTIALS", config.get("ALLOW_CREDENTIALS", True)
)
allow_methods = os.getenv("ALLOW_METHODS", config.get("ALLOW_METHODS", ["*"]))
allow_headers = os.getenv("ALLOW_HEADERS", config.get("ALLOW_HEADERS", ["*"]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
)
