import yaml
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# load in the config file
with open("auth_config.yaml", "r") as f:
    config = yaml.safe_load(f)
    SECRET_KEY = config["SECRET_KEY"]
    ALGORITHM = config["ALGORITHM"]
    TOKEN_URL = config["TOKEN_URL"]
    TOKEN_EXPIRATION_TIME = config["TOKEN_EXPIRATION_TIME"]
    EXPIRED_TOKENS_CLEANER_INTERVAL = TOKEN_EXPIRATION_TIME * 60
    SQLALCHEMY_DATABASE_URL = config["SQLALCHEMY_DATABASE_URL"]

# create the engine, session, and base
Engine = create_engine(SQLALCHEMY_DATABASE_URL)
AuthSession = sessionmaker(autocommit=False, autoflush=False, bind=Engine)
Base = declarative_base()

# create the password context, oauth2 scheme, and get_db function
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

def get_db():
    db = AuthSession()
    try:
        yield db
    finally:
        db.close()
