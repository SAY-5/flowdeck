"""Runtime configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings."""

    model_config = SettingsConfigDict(env_prefix="FLOWDECK_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://flowdeck:flowdeck@localhost:5432/flowdeck"
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    enable_reflection: bool = True
    max_page_size: int = 200
    default_page_size: int = 50


def get_settings() -> Settings:
    return Settings()
