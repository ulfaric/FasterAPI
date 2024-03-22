from sqlalchemy import Column, Integer
import uvicorn
from fastapi import APIRouter
from FasterAPI.app import app
from FasterAPI.utils import create_superuser
from FasterAPI.models import Base

class MyModels(Base):
    __tablename__ = "my_models"
    id = Column(Integer, primary_key=True, index=True)
    
router = APIRouter()

@router.get("/")
async def read_root():
    return {"Hello": "World"}

app.include_router(router, prefix="/my_models", tags=["my_models"])

if __name__ == "__main__":
    create_superuser(
        username="admin",
        password="admin",
        first_name="admin",
        last_name="admin",
        email="admin@admin.com"
    )
    uvicorn.run("FasterAPI.app:app", host="127.0.0.1", port=9000, log_level="info")