import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import load_config
from .router import auth_router
from .utils import auth_startup

meta_config = load_config("meta_config.yaml")
config = load_config("auth_config.yaml")

app = FastAPI(
    debug=meta_config.get("DEBUG", False),
    title=meta_config.get("TITLE", "FasterAPI"),
    description=meta_config.get(
        "DESCRIPTION",
        "A FastAPI starter template with prebuilt JWT auth system.",
    ),
    version=meta_config.get("VERSION", "0.0.1"),
    openapi_url=meta_config.get("OPENAPI_URL", "/openapi.json"),
    docs_url=meta_config.get("DOCS_URL", "/docs"),
    redoc_url=meta_config.get("REDOC_URL", "/redoc"),
    terms_of_service=meta_config.get("TERMS_OF_SERVICE", None),
    contact=meta_config.get("CONTACT", None),
    summary=meta_config.get("SUMMARY", None),
    on_startup=[lambda: asyncio.create_task(auth_startup())],
)

allow_origins = config.get("ALLOWED_ORIGINS", ["*"])
allow_credentials = config.get("ALLOW_CREDENTIALS", False)
allow_methods = config.get("ALLOW_METHODS", ["*"])
allow_headers = config.get("ALLOW_HEADERS", ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
)

app.include_router(auth_router)
