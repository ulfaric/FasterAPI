import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from . import config, load_config
from .router import auth_router
from .utils import auth_startup

meta_config = load_config("meta_config.yaml")


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
    on_startup=[lambda: asyncio.create_task(auth_startup())],
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
