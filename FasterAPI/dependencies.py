from datetime import datetime
from typing import Annotated, Any, List

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import ALGORITHM, SECRET_KEY, get_db, oauth2_scheme
from .models import BlacklistedToken, User


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
