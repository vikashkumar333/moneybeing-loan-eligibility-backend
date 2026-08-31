from typing import List, Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from models.user import User
from repositories.user_repository import UserRepository
from core.security import decode_access_token
from core.exceptions import AuthenticationException, AuthorizationException

# HTTPBearer security scheme enables Authorize 🔒 in FastAPI Swagger UI
security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise AuthenticationException("Authorization header with Bearer token is required")

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationException("Invalid, expired, or malformed authentication token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Token payload missing subject identifier")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise AuthenticationException("Invalid subject identifier in token")

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationException("Authenticated user no longer exists")

    if not user.is_active:
        raise AuthenticationException("User account is disabled")

    return user


def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_upper = current_user.role.upper()
        normalized_allowed = [r.upper() for r in allowed_roles]
        if user_role_upper not in normalized_allowed:
            raise AuthorizationException("You do not have permission to access this resource")
        return current_user

    return role_checker


def require_admin(current_user: User = Depends(require_roles(["Admin", "ADMIN"]))) -> User:
    return current_user
