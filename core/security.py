import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import JWTError, jwt
from app.config import settings


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def get_password_hash(password: str) -> str:
    return hash_password(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
    }
    if claims:
        to_encode.update(claims)

    secret = settings.JWT_SECRET_KEY or settings.SECRET_KEY
    algorithm = settings.JWT_ALGORITHM or settings.ALGORITHM
    return jwt.encode(to_encode, secret, algorithm=algorithm)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        secret = settings.JWT_SECRET_KEY or settings.SECRET_KEY
        algorithm = settings.JWT_ALGORITHM or settings.ALGORITHM
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
    except JWTError:
        return None
