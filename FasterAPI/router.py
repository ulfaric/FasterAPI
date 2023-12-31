from typing import List

import yaml
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from . import TOKEN_URL, get_db, oauth2_scheme, pwd_context
from .models import User, UserPrivilege
from .schemas import UserCreate, UserInfo, UserUpdate
from .utils import (
    authenticate_user,
    authenticated,
    blacklist_token,
    create_access_token,
    is_superuser,
    register_user,
)

with open("auth_config.yaml", "r") as f:
    config = yaml.safe_load(f)
    try:
        ALLOW_SELF_REGISTRATION = config["ALLOW_SELF_REGISTRATION"]
    except KeyError:
        ALLOW_SELF_REGISTRATION = True

auth_router = APIRouter()


@auth_router.post(f"/{TOKEN_URL}", tags=["Authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Authenticate a user and return a JWT access token"""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post(f"/logout", tags=["Authentication"], status_code=status.HTTP_200_OK)
async def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Logout a user and blacklisting their JWT access token"""
    try:
        blacklist_token(token, db)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid JWT token",
        )
    return {"detail": "Successfully logged out"}


if ALLOW_SELF_REGISTRATION:

    @auth_router.post("/users/create", tags=["Users"])
    async def register_user_self_signup(
        new_user: UserCreate, db: Session = Depends(get_db)
    ):
        """Register a new user"""
        register_user(new_user, db)
        return {"detail": "user successfully registered"}

else:

    @auth_router.post("/users/create", tags=["Users"])
    async def register_user_only_by_superuser(
        new_user: UserCreate,
        db: Session = Depends(get_db),
        user: User = Depends(is_superuser),
    ):
        """Register a new user"""
        register_user(new_user, db)
        return {"detail": "user successfully registered"}


@auth_router.get("/users/me", tags=["Users"], response_model=UserInfo)
async def get_user(user: User = Depends(authenticated), db: Session = Depends(get_db)):
    """Return the current user"""
    return user


if ALLOW_SELF_REGISTRATION:

    @auth_router.patch(
        "/users/update/{username}", tags=["Users"], response_model=UserInfo
    )
    async def update_user(
        username: str,
        new_userinfo: UserUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(authenticated),
    ):
        """Update a user's information"""
        existing_user = db.query(User).filter(User.username == username).first()
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        existing_user.first_name = new_userinfo.first_name  # type: ignore
        existing_user.last_name = new_userinfo.last_name  # type: ignore
        existing_user.email = new_userinfo.email  # type: ignore
        existing_user.hashed_password = pwd_context.hash(new_userinfo.password)  # type: ignore
        db.commit()
        return existing_user

else:

    @auth_router.patch(
        "/users/update/{username}", tags=["Users"], response_model=UserInfo
    )
    async def update_user(
        username: str,
        new_userinfo: UserUpdate,
        db: Session = Depends(get_db),
        user: User = Depends(is_superuser),
    ):
        """Update a user's information"""
        existing_user = db.query(User).filter(User.username == username).first()
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        existing_user.first_name = new_userinfo.first_name  # type: ignore
        existing_user.last_name = new_userinfo.last_name  # type: ignore
        existing_user.email = new_userinfo.email  # type: ignore
        existing_user.hashed_password = pwd_context.hash(new_userinfo.password)  # type: ignore
        db.commit()
        return existing_user


@auth_router.post("/users/promote/{username}", tags=["Users"], response_model=UserInfo)
async def promote_user(
    username: str, db: Session = Depends(get_db), user: User = Depends(is_superuser)
):
    """Promote a user to superuser"""
    existing_user = db.query(User).filter(User.username == username).first()
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    existing_user.is_superuser = True  # type: ignore
    db.commit()
    return existing_user


@auth_router.delete("/users/demote/{username}", tags=["Users"], response_model=UserInfo)
async def demote_user(
    username: str, db: Session = Depends(get_db), user: User = Depends(is_superuser)
):
    """Demote a user to normal user"""
    existing_user = db.query(User).filter(User.username == username).first()
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    existing_user.is_superuser = False  # type: ignore
    db.commit()
    return existing_user


@auth_router.post("/users/privilege/add", tags=["Users"], response_model=UserInfo)
async def add_privilege(
    username: str,
    privilege: str,
    db: Session = Depends(get_db),
    user: User = Depends(is_superuser),
):
    """Add a privilege to a user"""
    existing_user = db.query(User).filter(User.username == username).first()
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    new_privilege = UserPrivilege(user_id=existing_user.id, privilege=privilege)
    db.add(new_privilege)
    db.commit()
    return existing_user


@auth_router.post("/users/privilege/remove", tags=["Users"], response_model=UserInfo)
async def remove_privilege(
    username: str,
    privilege: str,
    db: Session = Depends(get_db),
    user: User = Depends(is_superuser),
):
    """Remove a privilege from a user"""
    existing_user = db.query(User).filter(User.username == username).first()
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    existing_privilege = (
        db.query(UserPrivilege)
        .filter(UserPrivilege.user_id == existing_user.id)
        .filter(UserPrivilege.privilege == privilege)
        .first()
    )
    if not existing_privilege:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Privilege not found",
        )
    db.delete(existing_privilege)
    db.commit()
    return existing_user


@auth_router.delete("/users/delete/{username}", tags=["Users"], response_model=UserInfo)
async def delete_user(
    username: str, db: Session = Depends(get_db), user: User = Depends(is_superuser)
):
    """Delete a user"""
    existing_user = db.query(User).filter(User.username == username).first()
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    db.delete(existing_user)
    db.commit()
    return existing_user


@auth_router.get("/users/all", tags=["Users"], response_model=list[UserInfo])
async def get_all_users(
    db: Session = Depends(get_db), user: User = Depends(is_superuser)
):
    """Get all users"""
    return db.query(User).all()


@auth_router.post("/users/verify/privilege/", tags=["Users"])
async def verify_user_privilege(
    privileges: List[str],
    db: Session = Depends(get_db),
    user: User = Depends(authenticated),
):
    """Verify a user's privilege(s)."""
    granted_privileges = (
        db.query(UserPrivilege).filter(UserPrivilege.user_id == user.id).all()
    )
    granted_privileges = [privilege.privilege for privilege in granted_privileges]
    if set(privileges).issubset(set(granted_privileges)):
        return Response(status_code=status.HTTP_200_OK)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The user doesn't have the required privileges",
        )
    
    
