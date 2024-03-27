import os
import secrets
from typing import Dict

import yaml
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from FasterAPI import Module, core

user_module = Module()
core.modules.append(user_module)

config: Dict = yaml.safe_load(
    open(os.path.join(os.path.dirname(__file__), "config.yaml"), "r")
) or {}

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
