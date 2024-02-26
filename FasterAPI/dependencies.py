from datetime import datetime
from typing import Annotated, Any, List

from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import ALGORITHM, ALLOW_MULTI_SESSIONS, SECRET_KEY, get_db, oauth2_scheme
from .models import BlacklistedToken, User, UserPrivilege, ActiveSession


async def authenticated(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):
    """A dependency function to authenticate the user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    multi_session_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Multiple sessions are not allowed",
        headers={"WWW-Authenticate": "Bearer"},
    )
    scope_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Insufficient privileges",
        headers={"WWW-Authenticate": "Bearer"},
    )
    jwt_exception = HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Invalid JWT token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    jwt_expired_exception = HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="JWT token has expired",
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
        scopes: List[str] = payload["scopes"]
        expiration = datetime.fromtimestamp(payload["exp"])
    except JWTError:
        raise jwt_exception
    if expiration < datetime.now():
        raise jwt_expired_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    user_privileges = db.query(UserPrivilege).filter(UserPrivilege.user_id == user.id).all()  # type: ignore
    user_scopes = [privilege.scope for privilege in user_privileges]
    if not set(scopes).issubset(set(user_scopes)):
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


class Privilegeverifier:
    """A dependency to check if the user has the required privileges."""

    def __init__(self, privileges: List[str]) -> None:
        self._required_privileges = privileges

    def __call__(self, privileges: List[str]) -> Any:
        if set(privileges).issubset(set(self.required_privileges)):
            return True
        else:
            missing_privileges = set(self.required_privileges).difference(
                set(privileges)
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"The user doesn't have all required privileges, missing: {missing_privileges}",
            )

    @property
    def required_privileges(self):
        """Returns the required privileges."""
        return self._required_privileges
