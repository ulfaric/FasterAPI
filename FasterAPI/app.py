import asyncio

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import auth_router
from .utils import auth_startup

app = FastAPI()

with open("auth_config.yaml", "r") as f:
    config = yaml.safe_load(f)
    try:
        origins = config["ALLOWED_ORIGINS"]
    except KeyError:
        origins = ["*"]
    try:
        allow_credentials = config["ALLOW_CREDENTIALS"]
    except KeyError:
        allow_credentials = False
    try:
        allow_methods = config["ALLOW_METHODS"]
    except KeyError:
        allow_methods = ["*"]
    try:
        allow_headers = config["ALLOW_HEADERS"]
    except KeyError:
        allow_headers = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
)

app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auth_startup())
