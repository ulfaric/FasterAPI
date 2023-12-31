import logging
import os
import secrets
from datetime import datetime
import socket

import colorlog
import yaml
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Default values
DEFAULT_ALGORITHM = "HS256"
DEFAULT_TOKEN_URL = "/login"
DEFAULT_TOKEN_EXPIRATION_TIME = 15

# set up logging
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


# Load configuration
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

# set up database
SQLALCHEMY_DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL", config.get("SQLALCHEMY_DATABASE_URL")
)

if SQLALCHEMY_DATABASE_URL is None:
    raise Exception("SQLALCHEMY_DATABASE_URL is not set.")

Engine = create_engine(SQLALCHEMY_DATABASE_URL)
AuthSession = sessionmaker(autocommit=False, autoflush=False, bind=Engine)
Base = declarative_base()


def get_db():
    db = AuthSession()
    try:
        yield db
    finally:
        db.close()


class SecretKey(Base):
    __tablename__ = "secret_keys"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True)
    secret_key = Column(String)
    created_at = Column(DateTime, default=datetime.now())


# assign values from config or environment variables
db = AuthSession()
Base.metadata.create_all(bind=Engine)
existing_secret_key = db.query(SecretKey).filter(SecretKey.hostname == socket.gethostname()).first()
if existing_secret_key:
    SECRET_KEY = os.getenv("SECRET_KEY", config.get("SECRET_KEY", existing_secret_key))
    if SECRET_KEY != existing_secret_key.secret_key:
        existing_secret_key.secret_key = SECRET_KEY # type: ignore
        db.commit()
else:
    SECRET_KEY = os.getenv("SECRET_KEY", config.get("SECRET_KEY", secrets.token_hex(32)))
    db.add(SecretKey(hostname=socket.gethostname(), secret_key=SECRET_KEY))
    db.commit()  
db.close()

ALGORITHM = os.getenv("ALGORITHM", config.get("ALGORITHM", DEFAULT_ALGORITHM))
TOKEN_URL = os.getenv("TOKEN_URL", config.get("TOKEN_URL", DEFAULT_TOKEN_URL))
TOKEN_EXPIRATION_TIME = int(
    os.getenv(
        "TOKEN_EXPIRATION_TIME",
        config.get("TOKEN_EXPIRATION_TIME", DEFAULT_TOKEN_EXPIRATION_TIME),
    )
)
EXPIRED_TOKENS_CLEANER_INTERVAL = TOKEN_EXPIRATION_TIME * 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)
