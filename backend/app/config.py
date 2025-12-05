from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Face Access Control"
    secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 30
    refresh_exp_minutes: int = 7 * 24 * 60
    database_url: str = "sqlite:///./data/app.db"
    embeddings_dir: str = "data/embeddings"
    embedder_name: str = "facenet"
    cors_origins: list[str] = ["*"]
    throttling_per_minute: int = 60
    threshold: float = 0.6
    gpio_pin: int = 17
    gpio_pulse_ms: int = 800
    sync_interval_sec: int = 300
    default_admin_identifier: str = "admin"
    default_admin_password: str = "admin"

    @field_validator("default_admin_password")
    @classmethod
    def limit_admin_password(cls, v: str) -> str:
        encoded = v.encode("utf-8")
        if len(encoded) <= 72:
            return v
        return encoded[:72].decode("utf-8", errors="ignore")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
