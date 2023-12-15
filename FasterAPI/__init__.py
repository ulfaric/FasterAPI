import logging
import os
import secrets

import colorlog
import yaml
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Default values
DEFAULT_ALGORITHM = "HS256"
DEFAULT_TOKEN_URL = "/login"
DEFAULT_TOKEN_EXPIRATION_TIME = 15


logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)

# Define log colors
cformat = "%(log_color)s%(levelname)s:  %(message)s"
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


def load_config(file_path):
    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warn(
            f"Configuration file {file_path} not found. Default configuration will be used."
        )
        return {}
    except PermissionError:
        logger.warn(
            f"No permission to read the file {file_path}. Default configuration will be used."
        )
        return {}
    return config


config = load_config("auth_config.yaml")

if config is None:
    raise Exception("Configuration file can not be loaded.")

SECRET_KEY = os.getenv("SECRET_KEY", config.get("SECRET_KEY", secrets.token_hex(32)))
ALGORITHM = os.getenv("ALGORITHM", config.get("ALGORITHM", DEFAULT_ALGORITHM))
TOKEN_URL = os.getenv("TOKEN_URL", config.get("TOKEN_URL", DEFAULT_TOKEN_URL))
TOKEN_EXPIRATION_TIME = int(
    os.getenv(
        "TOKEN_EXPIRATION_TIME",
        config.get("TOKEN_EXPIRATION_TIME", DEFAULT_TOKEN_EXPIRATION_TIME),
    )
)
EXPIRED_TOKENS_CLEANER_INTERVAL = TOKEN_EXPIRATION_TIME * 60
SQLALCHEMY_DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL", config.get("SQLALCHEMY_DATABASE_URL")
)

if SQLALCHEMY_DATABASE_URL is None:
    raise Exception("SQLALCHEMY_DATABASE_URL is not set.")

Engine = create_engine(SQLALCHEMY_DATABASE_URL)
AuthSession = sessionmaker(autocommit=False, autoflush=False, bind=Engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)


def get_db():
    db = AuthSession()
    try:
        yield db
    finally:
        db.close()
