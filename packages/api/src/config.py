"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "MobileDroid API"
    app_version: str = "0.1.0"
    debug: bool = False
    git_commit_sha: str = "unknown"  # Set at build time via environment
    commit_sha: str = "unknown"  # Alias for backwards compatibility

    def model_post_init(self, __context) -> None:
        """Set commit_sha from git_commit_sha after initialization."""
        if self.git_commit_sha != "unknown":
            object.__setattr__(self, "commit_sha", self.git_commit_sha)

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://mobiledroid:mobiledroid@db:5432/mobiledroid"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Docker
    docker_network: str = "mobiledroid_network"
    redroid_image: str = "mobiledroid/redroid-custom:latest"

    # ADB
    adb_host: str = "localhost"
    adb_port: int = 5037

    # ws-scrcpy
    scrcpy_host: str = "localhost"
    scrcpy_port: int = 8886

    # Security
    api_secret_key: str = "change-me-in-production"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours

    # LLM Providers
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    default_llm_provider: Literal["anthropic", "openai", "google"] = "anthropic"
    default_llm_model: str = "claude-sonnet-4-20250514"

    # Fingerprints
    fingerprints_path: str = "./config/fingerprints/devices.json"

    # Proxy defaults
    default_proxy_type: Literal["none", "http", "socks5"] = "none"
    default_proxy_host: str | None = None
    default_proxy_port: int | None = None
    default_proxy_username: str | None = None
    default_proxy_password: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
