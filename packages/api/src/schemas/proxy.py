"""Proxy schemas."""

import re
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


class ProxyResponse(BaseModel):
    """Schema for proxy response."""

    id: int
    protocol: str
    host: str
    port: int
    username: str | None
    password: str | None
    name: str | None
    country: str | None
    is_active: bool
    last_used_at: datetime | None
    times_used: int
    is_working: bool | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProxyCreate(BaseModel):
    """Schema for creating a proxy."""

    protocol: Literal["http", "socks5"] = "http"
    host: str
    port: int = Field(..., ge=1, le=65535)
    username: str | None = None
    password: str | None = None
    name: str | None = None
    country: str | None = None


class ProxyUpdate(BaseModel):
    """Schema for updating a proxy."""

    protocol: Literal["http", "socks5"] | None = None
    host: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    username: str | None = None
    password: str | None = None
    name: str | None = None
    country: str | None = None
    is_active: bool | None = None


class ProxyListResponse(BaseModel):
    """Schema for proxy list response."""

    proxies: list[ProxyResponse]
    total: int


class ProxyUploadResponse(BaseModel):
    """Schema for proxy upload response."""

    imported: int
    skipped: int
    errors: list[str]


def parse_proxy_line(line: str) -> dict | None:
    """Parse a proxy line in various formats.

    Supported formats:
    - host:port
    - host:port:username:password
    - username:password@host:port
    - protocol://host:port
    - protocol://username:password@host:port
    - socks5://host:port
    - http://host:port
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    protocol = "http"
    host = None
    port = None
    username = None
    password = None

    # Check for protocol prefix
    protocol_match = re.match(r'^(https?|socks5)://', line, re.IGNORECASE)
    if protocol_match:
        protocol = protocol_match.group(1).lower()
        if protocol == "https":
            protocol = "http"
        line = line[len(protocol_match.group(0)):]

    # Check for username:password@host:port format
    if "@" in line:
        auth_part, host_part = line.rsplit("@", 1)
        if ":" in auth_part:
            username, password = auth_part.split(":", 1)
        line = host_part

    # Parse host:port or host:port:username:password
    parts = line.split(":")

    if len(parts) == 2:
        # host:port
        host, port_str = parts
        try:
            port = int(port_str)
        except ValueError:
            return None
    elif len(parts) == 4:
        # host:port:username:password
        host, port_str, username, password = parts
        try:
            port = int(port_str)
        except ValueError:
            return None
    elif len(parts) >= 2:
        # Try to find port (first numeric value after host)
        host = parts[0]
        for i, p in enumerate(parts[1:], 1):
            try:
                port = int(p)
                # Remaining parts might be auth
                if i + 1 < len(parts):
                    username = parts[i + 1]
                if i + 2 < len(parts):
                    password = parts[i + 2]
                break
            except ValueError:
                continue
    else:
        return None

    if not host or not port:
        return None

    # Validate port range
    if port < 1 or port > 65535:
        return None

    return {
        "protocol": protocol,
        "host": host,
        "port": port,
        "username": username if username else None,
        "password": password if password else None,
    }
