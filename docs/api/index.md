# Installation

```python
pip install -U FasterAPI
```

All dependencies will be automatically installed, this includes everything from [FastAPI](https://fastapi.tiangolo.com/). The SQL driver is using `psycopg2-binary`. 

To start with default configuration, simply create a python file with the following content:

```python
import uvicorn
from FasterAPI.utils import init_migration, create_superuser

if __name__ == "__main__":
    # create a superuser, optional
    create_superuser(
        username="admin",
        password="admin",
        first_name="admin",
        last_name="admin",
        email="admin@admin.com"
    )
    # start the fastapi app
    uvicorn.run("FasterAPI:app", host="127.0.0.1", log_level="info", reload=True)
```

Now you have a backend with JWT authentication pipeline up and running!
