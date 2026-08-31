from datetime import timedelta
from typing import Tuple
from sqlalchemy.orm import Session
from models.user import User
from repositories.user_repository import UserRepository
from core.security import verify_password, create_access_token
from core.exceptions import AuthenticationException
from app.config import settings


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def authenticate_user(self, username: str, password: str) -> User:
        user = self.user_repo.get_by_username(username.strip())
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationException("Invalid username or password")

        if not user.is_active:
            raise AuthenticationException("User account is disabled. Please contact administrator.")

        self.user_repo.update_last_login(user.id)
        return user

    def generate_token_for_user(self, user: User) -> Tuple[str, int]:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_seconds = int(expires_delta.total_seconds())

        claims = {
            "role": user.role,
            "username": user.username,
        }
        access_token = create_access_token(
            subject=str(user.id),
            claims=claims,
            expires_delta=expires_delta,
        )
        return access_token, expires_seconds
