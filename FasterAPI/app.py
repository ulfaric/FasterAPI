import asyncio
import os
import pickle
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from . import Engine, config, get_db, logger, meta_config
from .models import Base, User
from .router import auth_router
from .utils import _clean_up_expired_tokens, register_user


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
                    register_user(superuser)
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
                    register_user(user)
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
allow_credentials = bool(
    os.getenv("ALLOW_CREDENTIALS", config.get("ALLOW_CREDENTIALS", True))
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

app.include_router(auth_router, tags=["Authentication"])

if meta_config.get("JAEGER_TRACE", False):
    jaeger_exporter = JaegerExporter(
        # configure the hostname and port of your Jaeger instance here
        agent_host_name=meta_config.get("JAEGER_HOST", "localhost"),
        agent_port=meta_config.get("JAEGER_PORT", 6831),
    )

    trace_provider = TracerProvider(
        resource=Resource(
            attributes={"service.name": meta_config.get("JAEGER_SVC_NAME", "FasterAPI")}
        )
    )
    trace_provider.add_span_processor(SimpleSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(tracer_provider=trace_provider)
    FastAPIInstrumentor().instrument_app(app)
