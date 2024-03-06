import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from contextlib import asynccontextmanager
from . import config, meta_config, Base, Engine, users, superusers, AuthSession, logger
from .router import auth_router
from .utils import clean_up_expired_tokens, register_user
from .models import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=Engine)
    logger.debug("Database initialized.")
    db = AuthSession()
    for user in users:
        existing_user = db.query(User).filter(User.username == user.username).first()
        if not existing_user:
            register_user(user, db)
    for superuser in superusers:
        existing_user = db.query(User).filter(User.username == superuser.username).first()
        if not existing_user:
            register_user(superuser, db)
    db.close()
    logger.debug("Users registered.")
    expired_token_cleaner = asyncio.create_task(clean_up_expired_tokens())
    yield
    expired_token_cleaner.cancel()


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
    lifespan=lifespan,
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

app.include_router(auth_router)
