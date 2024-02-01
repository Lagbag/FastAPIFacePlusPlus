from fastapi.params import Query
from pydantic import BaseModel, Field
from typing import Annotated, Union
from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class BaseUser(BaseModel):
    username: str = Field(description="Username")
    email: Union[str, None] = None
    is_active: Union[bool, None] = None