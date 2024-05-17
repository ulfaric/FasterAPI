# Configuration

With FasterAPI, you could quickly configure your application via two files: `auth_config.yaml` and `meta_config.yaml`. These two files must sit besides your `main script`, such as the one shown under `Getting Started`. Otherwise, FasterAPI will use all default configurations. Note that you could also use envrionment variables but they will be overwrittern if configuration file exits.

## auth_config.yaml

Here are all the keys for `auth_config.yaml`:

```yaml
SQLALCHEMY_DATABASE_URL: 'sqlite:///dev.db' # "postgresql://<username>:<password>@HOST:PORT/test"
SECRET_KEY: # random secret key for JWT creation, you can run openssl rand 32
ALGORITHM: "HS256" # hashing algorithm
TOKEN_URL: "login" # url for user login
TOKEN_EXPIRATION_TIME: 1 # JWT token expiration time in minutes
ALLOW_SELF_REGISTRATION: False # if true, anyone could register a user without autehntication, otherwise only superuser can do so.

# following fields related to COSRF
ALLOW_CREDENTIALS: False
ALLOWED_ORIGINS:
  - "*"
ALLOWED_METHODS:
  - "*"
ALLOWED_HEADERS:
  - "*"
```

## meta_config.yaml

Here are the keys for `meta_config.yaml`:

```yaml
DEBUG: True
TITLE: "My API"
DESCRIPTION: "This is a description of my API"
VERSION: "0.0.2"
OPENAPI_URL: "/openapi.json"
DOCS_URL: "/docs"
REDOC_URL: "/redoc"
TERMS_OF_SERVICE: ""
CONTACT: ""
SUMMARY: "This is a summary of my API"

TRACE: True # enable tracing
SVC_NAME: "my-api" # service name
TRACE_ENDPOINT: "192.168.5.3:4317" # otlp rgpc endpoint
```
