# describes the API's input/output shape. 
# It's about what data looks like going in and out over the network.

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ---------- Auth ----------

class UserCreate(BaseModel):
    """What the client must send to register a new user."""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """What the client must send to log in."""
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """What we send back about a user (never includes the password!)."""
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # lets this read directly from a SQLAlchemy model


class Token(BaseModel):
    """What we send back after a successful login."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """What we decode out of a JWT token internally."""
    email: Optional[str] = None