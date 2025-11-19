"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App Configuration
    app_name: str = "Forecast Studio"
    debug: bool = False
    version: str = "0.1.0"

    # Database
    database_url: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]

    # File Upload
    max_upload_size: int = 52428800  # 50MB
    upload_dir: str = "./uploads"

    # Forecasting Defaults
    default_forecast_horizon: int = 12
    default_confidence_level: int = 90

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
