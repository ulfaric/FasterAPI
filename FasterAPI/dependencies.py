from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import SecurityScopes
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .essentials import ALGORITHM, ALLOW_MULTI_SESSIONS, SECRET_KEY, get_db, oauth2_scheme
from .models import ActiveSession, BlacklistedToken, User


async def authenticated(
    request: Request,
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):
    """A dependency function to authenticate the user."""

    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    multi_session_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Multiple sessions are not allowed",
        headers={"WWW-Authenticate": authenticate_value},
    )
    scope_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Insufficient privileges",
        headers={"WWW-Authenticate": authenticate_value},
    )
    jwt_exception = HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Invalid JWT token",
        headers={"WWW-Authenticate": authenticate_value},
    )
    jwt_expired_exception = HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="JWT token has expired",
        headers={"WWW-Authenticate": authenticate_value},
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
    except JWTError:
        raise jwt_exception
    if expiration < datetime.now():
        raise jwt_expired_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    user_privileges = [privilege.privilege for privilege in user.privileges]
    if not set(security_scopes.scopes).issubset(set(user_privileges)):
        raise scope_exception
    active_session = (
        db.query(ActiveSession).filter(ActiveSession.username == username).first()
    )
    if ALLOW_MULTI_SESSIONS is False:
        if request.client.host != str(active_session.client):  # type: ignore
            raise multi_session_exception
    return user


async def is_superuser(user: Annotated[User, Depends(authenticated)]):
    """A dependency function to check if the user is a superuser."""
    if not user.is_superuser:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user doesn't have enough privileges",
        )
    return user
