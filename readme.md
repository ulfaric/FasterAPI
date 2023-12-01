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
ALLOWED_ORIGINS: # Here goes your allowed origns for CSRF protection
  - "*"
```
Now, create a "app.py" file:
```
from FasterAPI.utils import create_superuser
from FasterAPI.app import app

# create the super user
create_superuser(
    username="admin",
    password="admin",
    email="email@email.com",
    first_name="admin",
    last_name="admin",
)

# refrence to the FastAPI app instance
Myapp = app
```
Finally, you could start the application by:
```
uvicorn app:Myapp --reload
```
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