from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="Account username")
    password: str = Field(..., min_length=1, description="Account password")


class LoginResponse(BaseModel):
    status: str = Field(default="success")
    access_token: str = Field(..., description="JWT Bearer access token")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Token lifespan in seconds")


class TokenResponse(LoginResponse):
    pass


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime


class UserResponse(CurrentUserResponse):
    pass


class AdminCheckResponse(BaseModel):
    status: str = Field(default="success")
    message: str = Field(default="Admin access granted")


class LogoutResponse(BaseModel):
    status: str = Field(default="success")
    message: str = Field(default="Logged out successfully")
