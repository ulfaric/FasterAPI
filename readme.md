# FasterAPI

This is a simple start point for backend application based on FastAPI with JWT user authentication built for you. :)

## How to use

First install it with pip. You do not need to install FastAPI seperately. All related libaray has been added as dependencies.

```[python]
pip install FasterAPI
```
Then, you have to create a "auth-config.yaml" file, please make sure the file name is excat the same. This file should contains:
```
SQLALCHEMY_DATABASE_URL: "postgresql://postgres:postgres@127.0.0.1:5432/postgres" # url to your postgresql
SECRET_KEY: "8cfba7f89fca29a5f86cd8e02cb5381070690e378fc26cce4a311f84ce93672a" # create with openssl rand -hex 32
ALGORITHM: "HS256" # encryption algorithm
TOKEN_URL: "login" # url for login
TOKEN_EXPIRATION_TIME: 1 # token expiration time in minutes.
ALLOW_SELF_REGISTRATION: True # if ture, anyone could register a user account. Otherwise, only superuser could.

# if any following configuration is missing, lowest security config will used for faster development!
# for non-website (include web app) you may want to use the default settings so your request won't be blocked.
ALLOW_CREDENTIALS: False # Here goes your choice for whether allow credential for CSRF protection
ALLOWED_ORIGINS: # Here goes your allowed origns for CSRF protection
  - "*"
ALLOWED_METHODS: # Here goes your allowed method for CSRF protection
  - "*"
ALLOWED_HEADERS: # Here goes your allowed headers for CSRF protection
  - "*"
```
Now, create a "main.py" file:
```
import uvicorn
from FasterAPI.utils import init_migration, create_superuser

if __name__ == "__main__":
    # must run at first which creates all tables within the database.
    init_migration()
    # create a superuser, optional
    create_superuser(
        username="admin",
        password="admin",
        first_name="admin",
        last_name="admin",
        email="admin@admin.com"
    )
    # start the fastapi app
    uvicorn.run("FasterAPI.app:app", host="127.0.0.1", log_level="info", reload=True)
```
Finally, you could start the application by simply run the main.py.

## Add additonal models and routes
If you need more models, you have to reference the base created inside FasterAPI:
```
from FasterAPI import Base
```
For your additional route, you have to reference the FasterAPI app instance like:
```
from FasterAPI.app import app

@app.get("/)
# your function goes here
```
Note that you will have to create a python module, place main.py and auth-config.yaml like following:
```
your_module:
  -- __init__.py
  -- models.py # your additional models
  -- schemas.py # your schemas
  -- routes.py # your addtional routes
main.py
auth_config.yaml
```
