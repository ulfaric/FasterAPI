import asyncio
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import (
    ALGORITHM,
    SECRET_KEY,
    TOKEN_EXPIRATION_TIME,
    AuthSession,
    Base,
    Engine,
    get_db,
    oauth2_scheme,
    pwd_context,
)
from .models import BlacklistedToken, User, UserPrivilege
from .schemas import UserCreate, Privilege

if TOKEN_EXPIRATION_TIME is None:
    raise Exception("TOKEN_EXPIRATION_TIME is not set.")


async def cleanup_expired_tokens():
    """A async task to cleanup expired tokens from the database. Maintains a optimal performance."""
    while True:
        db = AuthSession()
        db.query(BlacklistedToken).filter(
            BlacklistedToken.exp < datetime.now()
        ).delete()
        db.commit()
        db.close()
        await asyncio.sleep(TOKEN_EXPIRATION_TIME)


async def auth_startup():
    """Starts the cleanup_expired_tokens task on startup."""
    asyncio.create_task(cleanup_expired_tokens())


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
    role = Privilege(privilege="superuser")
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


async def authenticated(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):
    """A dependency function to authenticate the user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    jwt_exception = HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Invalid JWT token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    blacklisted_token = (
        db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
    )
    if blacklisted_token:
        raise jwt_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload["sub"]
        expiration = datetime.fromtimestamp(payload["exp"])
        if expiration < datetime.now():
            raise jwt_exception
        if username is None:
            raise credentials_exception
    except JWTError:
        raise jwt_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


async def is_superuser(user: Annotated[User, Depends(authenticated)]):
    """A dependency function to check if the user is a superuser."""
    if not user.is_superuser:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user doesn't have enough privileges",
        )
    return user


async def verify_user_privilege(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(authenticated)],
    privileges: list[str],
):
    """A dependency function to check if the user has the required privileges.""" ""
    granted_privileges = (
        db.query(UserPrivilege).filter(UserPrivilege.user_id == user.id).all()
    )
    granted_privileges = [privilege.privilege for privilege in granted_privileges]
    if set(privileges).issubset(set(granted_privileges)):
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user doesn't have enough privileges",
        )
