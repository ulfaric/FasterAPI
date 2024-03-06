import uvicorn
from FasterAPI.utils import init_migration, create_superuser

if __name__ == "__main__":
    create_superuser(
        username="admin",
        password="admin",
        first_name="admin",
        last_name="admin",
        email="admin@admin.com"
    )
    uvicorn.run("FasterAPI.app:app", host="127.0.0.1", port=9000, log_level="info", reload=True)
