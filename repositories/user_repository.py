from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from models.user import User
from core.security import get_password_hash


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def create(self, username: str, password: str, role: str = "Admin", is_active: bool = True) -> User:
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            password_hash=hashed_password,
            role=role,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_last_login(self, user_id: int) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(user)
        return user

    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()
