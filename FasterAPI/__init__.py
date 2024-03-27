import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Callable, Coroutine, Dict, List
import uvicorn
import colorlog
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
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


class Module:

    def __init__(self) -> None:
        config: Dict = yaml.safe_load(
            open("config.yaml", "r")
        )
        self._sql_url = os.getenv(
            "SQLALCHEMY_DATABASE_URL",
            config.get("SQLALCHEMY_DATABASE_URL", "sqlite:///dev.db"),
        )
        self._engine = create_engine(self._sql_url)
        self._session = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self._lifespan: Callable = None  # type: ignore

    def __call__(self):
        db = self.session()
        try:
            yield db
        finally:
            db.close()

    @property
    def engine(self):
        return self._engine

    @property
    def session(self):
        return self._session

    @property
    def lifespan(self):
        return self._lifespan


class Core:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):

        # define lifespan
        @asynccontextmanager
        async def _lifespan(app: FastAPI):
            for module in self._modules:
                self.sql_base.metadata.create_all(bind=module.engine)
            logger.debug("Database initialized.")
            lifespans: List[asyncio.Task] = list()
            for module in self.modules:
                if module.lifespan:
                    lifespans.append(asyncio.create_task(module.lifespan()))
            yield
            for lifespan in lifespans:
                lifespan.cancel()

        self._config = yaml.safe_load(open("config.yaml", "r"))
        self._modules: List[Module] = list()
        self._sql_base = declarative_base()
        self._app = FastAPI(
            debug=bool(os.getenv("DEBUG", self.config.get("DEBUG", False))),
            title=os.getenv("TITLE", self.config.get("TITLE", "FasterAPI")),
            description=os.getenv(
                "DESCRIPTION",
                self.config.get(
                    "DESCRIPTION",
                    "A FastAPI starter template with prebuilt JWT auth system.",
                ),
            ),
            version=os.getenv("VERSION", self.config.get("VERSION", "0.0.1")),
            openapi_url=os.getenv(
                "OPENAPI_URL", self.config.get("OPENAPI_URL", "/openapi.json")
            ),
            docs_url=os.getenv("DOCS_URL", self.config.get("DOCS_URL", "/docs")),
            redoc_url=os.getenv("REDOC_URL", self.config.get("REDOC_URL", "/redoc")),
            terms_of_service=os.getenv(
                "TERMS_OF_SERVICE", self.config.get("TERMS_OF_SERVICE", None)
            ),
            contact=os.getenv("CONTACT", self.config.get("CONTACT", None)),  # type: ignore
            summary=os.getenv("SUMMARY", self.config.get("SUMMARY", None)),
            lifespan=_lifespan,
        )

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=os.getenv(
                "ALLOWED_ORIGINS", self.config.get("ALLOWED_ORIGINS", ["*"])
            ),
            allow_credentials=bool(
                os.getenv(
                    "ALLOW_CREDENTIALS", self.config.get("ALLOW_CREDENTIALS", True)
                )
            ),
            allow_methods=os.getenv(
                "ALLOW_METHODS", self.config.get("ALLOW_METHODS", ["*"])
            ),
            allow_headers=os.getenv(
                "ALLOW_HEADERS", self.config.get("ALLOW_HEADERS", ["*"])
            ),
        )

        if self.config.get("JAEGER_TRACE", False):
            jaeger_exporter = JaegerExporter(
                # configure the hostname and port of your Jaeger instance here
                agent_host_name=self.config.get("JAEGER_HOST", "localhost"),
                agent_port=self.config.get("JAEGER_PORT", 6831),
            )

            trace_provider = TracerProvider(
                resource=Resource(
                    attributes={
                        "service.name": self.config.get("JAEGER_SVC_NAME", "FasterAPI")
                    }
                )
            )
            trace_provider.add_span_processor(SimpleSpanProcessor(jaeger_exporter))
            trace.set_tracer_provider(tracer_provider=trace_provider)
            FastAPIInstrumentor().instrument_app(self.app)

    def serve(self, port:int=8000, debug:bool=False):
        if debug:
            uvicorn.run(core.app, host="127.0.0.1", port=port, log_level="debug")
        else:
            uvicorn.run(core.app, host="0.0.0.0", port=port, log_level="info")
        
    @property
    def config(self) -> Dict:
        return self._config

    @property
    def app(self) -> FastAPI:
        return self._app

    @property
    def modules(self) -> List[Module]:
        return self._modules

    @property
    def sql_base(self):
        return self._sql_base


core = Core()
