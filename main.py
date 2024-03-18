from sqlalchemy import Column, Integer
import uvicorn
from FasterAPI.utils import create_superuser
from FasterAPI.models import Base

class MyModels(Base):
    __tablename__ = "my_models"
    id = Column(Integer, primary_key=True, index=True)

if __name__ == "__main__":
    create_superuser(
        username="admin",
        password="admin",
        first_name="admin",
        last_name="admin",
        email="admin@admin.com"
    )
    uvicorn.run("FasterAPI:app", host="127.0.0.1", port=9000, log_level="info")
