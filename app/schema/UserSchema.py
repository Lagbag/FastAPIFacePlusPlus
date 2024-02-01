from fastapi.params import Query
from pydantic import BaseModel, Field
from typing import Annotated, Union


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str = Field(description="Username")
    email: Union[str, None] = None
    is_active: Union[bool, None] = None
