from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from models.user import User
from services.auth_service import AuthService
from schemas.auth import (
    LoginRequest,
    LoginResponse,
    CurrentUserResponse,
    AdminCheckResponse,
    LogoutResponse,
)
from api.v1.auth.dependencies import get_current_user, require_admin
from core.responses import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse, summary="Admin Login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(username=request.username, password=request.password)
    access_token, expires_in = auth_service.generate_token_for_user(user)

    return LoginResponse(
        status="success",
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.get("/me", response_model=APIResponse[CurrentUserResponse], summary="Get Current Authenticated User")
def get_me(current_user: User = Depends(get_current_user)):
    return APIResponse(
        status="success",
        data=CurrentUserResponse.model_validate(current_user),
    )


@router.get("/admin-check", response_model=AdminCheckResponse, summary="Verify Admin Access")
def admin_check(admin: User = Depends(require_admin)):
    return AdminCheckResponse(
        status="success",
        message="Admin access granted",
    )


@router.post("/logout", response_model=LogoutResponse, summary="Logout User")
def logout(current_user: User = Depends(get_current_user)):
    return LogoutResponse(
        status="success",
        message="Logged out successfully",
    )
