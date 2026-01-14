"""Proxy pool database model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class Proxy(Base, TimestampMixin):
    """Proxy in the proxy pool."""

    __tablename__ = "proxies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Proxy details
    protocol: Mapped[str] = mapped_column(String(10), nullable=False, default="http")  # http, socks5
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Metadata
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Optional friendly name
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)  # ISO country code

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_working: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # Last check result

    # Usage tracking
    times_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        auth = f"{self.username}@" if self.username else ""
        return f"<Proxy {self.id}: {self.protocol}://{auth}{self.host}:{self.port}>"

    def to_url(self, include_auth: bool = True) -> str:
        """Convert proxy to URL format."""
        if include_auth and self.username:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"

    def to_config(self) -> dict:
        """Convert to profile proxy config format."""
        return {
            "type": self.protocol,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
        }
