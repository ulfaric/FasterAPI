import asyncio

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import auth_router
from .utils import auth_startup

app = FastAPI()

with open("auth_config.yaml", "r") as f:
    config = yaml.safe_load(f)
    origins = config["ALLOWED_ORIGINS"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auth_startup())
