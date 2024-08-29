import uuid

from pydantic import BaseModel, EmailStr
from src.schemas import TunedModel


class ShowUser(TunedModel):
    user_id: uuid.UUID
    user_name: str
    email: EmailStr
    is_active: bool


class UserCreate(BaseModel):
    user_name: str
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPair(BaseModel):
    access: str
    refresh: str
    token_type: str = "bearer"


class ChangePassword(TunedModel):
    old_password: str
    new_password: str