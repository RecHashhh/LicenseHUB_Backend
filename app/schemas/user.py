from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import RoleEnum


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: RoleEnum = RoleEnum.user
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: RoleEnum | None = None
    is_active: bool | None = None
    password: str | None = None


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
