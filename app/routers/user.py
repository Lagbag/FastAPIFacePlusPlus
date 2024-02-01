import os
from typing import List, Optional, Annotated
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from ..services.async_database import get_async_session
from ..services.auth import authenticate_user, create_access_token, get_current_active_user
from ..services.config import ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from ..schema.UserSchema import Token, BaseUser, UserRegister
from app.services.utils import pwd_context
from app.models.UserModel import User
from fastapi.responses import RedirectResponse

router = APIRouter(
    prefix="/user",
    tags=["user"],
    dependencies=[],
    responses={404: {"description": "Not found"}},

)

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_async_session)
):
    user = await authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me/")
async def read_users_me(
    current_user: Annotated[BaseUser, Depends(get_current_active_user)]
):
    return current_user


@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[BaseUser, Depends(get_current_active_user)]
):
    return [{"item_id": "Foo", "owner": current_user.username}]


@router.post("/register", response_model=UserRegister, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserRegister, session: AsyncSession = Depends(get_async_session)):
    db_user = await User.get_user_by_username(user.username, session)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    db_user = User(email=user.email, username=user.username, hashed_password=hashed_password)
    session.add(db_user)
    await session.commit()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)