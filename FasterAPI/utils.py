import asyncio
import pickle
from datetime import datetime, timedelta
from typing import List

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from .essentials import (ALGORITHM, SECRET_KEY, TOKEN_EXPIRATION_TIME, get_db, logger,
                         pwd_context)
from .models import ActiveSession, BlacklistedToken, User
from .schemas import UserCreate


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
        db.query(ActiveSession).filter(
            ActiveSession.username == username).first()
    )
    if existing_active_session:
        existing_active_session.client = client  # type: ignore
        existing_active_session.exp = exp  # type: ignore
        db.commit()
    else:
        token_to_activate = ActiveSession(
            username=username, client=client, exp=exp)
        db.add(token_to_activate)
        db.commit()


def blacklist_token(token: str, db: Session):
    """Blacklists the token upon user logout."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp = datetime.fromtimestamp(payload["exp"])
    token_to_blacklist = BlacklistedToken(token=token, exp=exp)
    db.add(token_to_blacklist)
    db.commit()


def register_user(user: UserCreate):
    """Registers a new user."""
    db = next(get_db())
    extsing_user = db.query(User).filter(
        User.username == user.username).first()
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
    logger.debug(f"User {user.username} registered.")
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

    def _load_superusers() -> List[UserCreate]:
        try:
            with open(".superuser", "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return []

    def _save_superusers(superusers: List[UserCreate]):
        with open(".superuser", "wb") as f:
            pickle.dump(superusers, f)

    superusers = _load_superusers()
    superusers.append(superuser)
    _save_superusers(superusers)


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

    def _load_users() -> List[UserCreate]:
        try:
            with open(".users", "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return []

    def _save_users(users: List[UserCreate]):
        with open(".users", "wb") as f:
            pickle.dump(users, f)

    users = _load_users()
    users.append(user)
    _save_users(users)


# define neccessary functions
async def _clean_up_expired_tokens():
    """A async task to cleanup expired tokens from the database. Maintains a optimal performance."""
    while True:
        db = next(get_db())
        db.query(BlacklistedToken).filter(
            BlacklistedToken.exp < datetime.now()
        ).delete()
        db.commit()
        db.close()
        logger.debug("Expired tokens cleaned up.")
        await asyncio.sleep(TOKEN_EXPIRATION_TIME * 60)
