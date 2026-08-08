from pydantic import BaseModel, EmailStr
import uuid


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    is_active: bool

    model_config = {
        "from_attributes": True
    }