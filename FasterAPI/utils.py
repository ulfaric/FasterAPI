import asyncio
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from . import (
    ALGORITHM,
    SECRET_KEY,
    TOKEN_EXPIRATION_TIME,
    AuthSession,
    Base,
    Engine,
    pwd_context,
)
from .models import BlacklistedToken, User, ActiveSession
from .schemas import UserCreate

if TOKEN_EXPIRATION_TIME is None:
    raise Exception("TOKEN_EXPIRATION_TIME is not set.")


async def clean_up_expired_tokens():
    """A async task to cleanup expired tokens from the database. Maintains a optimal performance."""
    while True:
        db = AuthSession()
        db.query(BlacklistedToken).filter(
            BlacklistedToken.exp < datetime.now()
        ).delete()
        db.commit()
        db.close()
        await asyncio.sleep(TOKEN_EXPIRATION_TIME)


def init_migration():
    """Initializes the database migration."""
    Base.metadata.create_all(bind=Engine)


def verify_password(plain_password, hashed_password):
    """Verifies the password."""
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(db: Session, username: str, password: str):
    """Authenticates the user."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


if SECRET_KEY is None:
    raise Exception("SECRET_KEY is not set.")


def create_access_token(data: dict):
    """Creates a JWT token for authenticated user."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION_TIME)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_session(token: str, db: Session, client: str):
    """Activates the token upon user login."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload["sub"]
    exp = datetime.fromtimestamp(payload["exp"])
    existing_active_session = (
        db.query(ActiveSession).filter(ActiveSession.username == username).first()
    )
    if existing_active_session:
        existing_active_session.client = client  # type: ignore
        existing_active_session.exp = exp  # type: ignore
        db.commit()
    else:
        token_to_activate = ActiveSession(username=username, client=client, exp=exp)
        db.add(token_to_activate)
        db.commit()


def blacklist_token(token: str, db: Session):
    """Blacklists the token upon user logout."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp = datetime.fromtimestamp(payload["exp"])
    token_to_blacklist = BlacklistedToken(token=token, exp=exp)
    db.add(token_to_blacklist)
    db.commit()


def register_user(user: UserCreate, db: Session):
    """Registers a new user."""
    extsing_user = db.query(User).filter(User.username == user.username).first()
    if extsing_user:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="User already exists.",
        )
    new_user = User(
        username=user.username,
        hashed_password=pwd_context.hash(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        is_superuser=user.is_superuser,
    )
    db.add(new_user)
    db.commit()
    return user


def create_superuser(
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    email: str,
):
    """Creates a superuser."""
    superuser = UserCreate(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        is_superuser=True,
    )
    db = AuthSession()
    existing_user = db.query(User).filter(User.username == superuser.username).first()
    if existing_user:
        db.close()
        return
    else:
        register_user(superuser, db)
        db.close()


def create_user(
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    email: str,
):
    """Creates a user."""
    user = UserCreate(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        is_superuser=False,
    )
    db = AuthSession()
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        db.close()
        return
    else:
        register_user(user, db)
        db.close()
