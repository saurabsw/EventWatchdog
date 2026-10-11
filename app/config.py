import logging
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "sqlite:///./data/app.db"
    VICTORIAMETRICS_URL: str = "http://localhost:8428"
    VICTORIAMETRICS_TIMEOUT_SECONDS: float = 5.0

    EVALUATION_INTERVAL_SECONDS: int = 15
    MODEL_TRAINING_MIN_SAMPLES: int = 50
    MAX_LOG_BATCH_SIZE_BYTES: int = 5242880
    ALLOWED_HOSTS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()


def setup_logging():
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ"
    )
