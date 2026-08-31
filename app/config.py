from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "MoneyBeing Loan Eligibility API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Server & CORS
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Security & JWT
    JWT_SECRET_KEY: str = "moneybeing-super-secret-jwt-key-min-32-chars-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Backward compatibility aliases
    SECRET_KEY: str = "moneybeing-super-secret-jwt-key-min-32-chars-change-in-prod"
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgrespassword@localhost:5432/moneybeing_db"

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True
    REDIS_CACHE_TTL_SECONDS: int = 300

    # Credit Score Integration
    CREDIT_SCORE_PROVIDER: str = "mock"
    CREDIT_SCORE_API_BASE_URL: str = "https://api.cibil.com/v1/score"
    CREDIT_SCORE_API_KEY: str = ""
    CREDIT_SCORE_API_TIMEOUT: float = 10.0
    MOCK_CREDIT_SCORE: int = 742

    # Backward compatibility aliases
    CIBIL_API_URL: str = "https://api.cibil.com/v1/score"
    CIBIL_API_KEY: str = ""
    CIBIL_CLIENT_ID: str = ""
    CIBIL_CLIENT_SECRET: str = ""
    CIBIL_TIMEOUT_SECONDS: float = 10.0

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()
