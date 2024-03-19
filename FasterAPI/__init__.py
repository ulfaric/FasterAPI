from __future__ import annotations

import logging
import os
import secrets

import colorlog
import yaml
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
