from fastapi import FastAPI
from .router import auth_router
from .utils import auth_startup
import asyncio


app = FastAPI()
app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auth_startup())