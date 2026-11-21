from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "BalanceFlow API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Base de datos (SQLite por ahora; cambiar a PostgreSQL en producción)
    DATABASE_URL: str = "sqlite:///./balanceflow.db"

    # JWT / Seguridad (cambiar SECRET_KEY en producción)
    SECRET_KEY: str = "balanceflow-hackathon-2026-cambia-esto"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()