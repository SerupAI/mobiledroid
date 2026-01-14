"""Proxy pool management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.db import get_db
from src.models.proxy import Proxy
from src.schemas.proxy import (
    ProxyResponse,
    ProxyCreate,
    ProxyUpdate,
    ProxyListResponse,
    ProxyUploadResponse,
    parse_proxy_line,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/proxies", tags=["proxies"])


@router.get("", response_model=ProxyListResponse)
async def list_proxies(
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
):
    """List all proxies in the pool."""
    query = select(Proxy)

    if active_only:
        query = query.where(Proxy.is_active == True)

    # Get total count
    count_query = select(func.count(Proxy.id))
    if active_only:
        count_query = count_query.where(Proxy.is_active == True)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get proxies
    query = query.order_by(Proxy.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    proxies = result.scalars().all()

    return ProxyListResponse(
        proxies=[ProxyResponse.model_validate(p) for p in proxies],
        total=total,
    )


@router.post("", response_model=ProxyResponse, status_code=status.HTTP_201_CREATED)
async def create_proxy(
    data: ProxyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add a single proxy to the pool."""
    # Check for duplicate
    existing = await db.execute(
        select(Proxy).where(
            Proxy.host == data.host,
            Proxy.port == data.port,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Proxy {data.host}:{data.port} already exists",
        )

    proxy = Proxy(**data.model_dump())
    db.add(proxy)
    await db.commit()
    await db.refresh(proxy)

    logger.info("Created proxy", proxy_id=proxy.id, host=proxy.host, port=proxy.port)
    return ProxyResponse.model_validate(proxy)


@router.post("/upload", response_model=ProxyUploadResponse)
async def upload_proxies(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file containing proxies (one per line).

    Supported formats:
    - host:port
    - host:port:username:password
    - username:password@host:port
    - protocol://host:port
    - protocol://username:password@host:port

    Lines starting with # are ignored.
    """
    content = await file.read()

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not decode file. Please use UTF-8 encoding.",
            )

    lines = text.splitlines()
    imported = 0
    skipped = 0
    errors = []

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parsed = parse_proxy_line(line)
        if not parsed:
            errors.append(f"Line {i}: Could not parse '{line[:50]}'")
            continue

        # Check for duplicate
        existing = await db.execute(
            select(Proxy).where(
                Proxy.host == parsed["host"],
                Proxy.port == parsed["port"],
            )
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        # Create proxy
        proxy = Proxy(**parsed)
        db.add(proxy)
        imported += 1

    await db.commit()

    logger.info(
        "Uploaded proxies",
        filename=file.filename,
        imported=imported,
        skipped=skipped,
        errors=len(errors),
    )

    return ProxyUploadResponse(
        imported=imported,
        skipped=skipped,
        errors=errors[:10],  # Limit errors in response
    )


@router.get("/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(
    proxy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific proxy."""
    result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
    proxy = result.scalar_one_or_none()

    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proxy {proxy_id} not found",
        )

    return ProxyResponse.model_validate(proxy)


@router.patch("/{proxy_id}", response_model=ProxyResponse)
async def update_proxy(
    proxy_id: int,
    data: ProxyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a proxy."""
    result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
    proxy = result.scalar_one_or_none()

    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proxy {proxy_id} not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proxy, field, value)

    await db.commit()
    await db.refresh(proxy)

    logger.info("Updated proxy", proxy_id=proxy_id)
    return ProxyResponse.model_validate(proxy)


@router.delete("/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proxy(
    proxy_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a proxy from the pool."""
    result = await db.execute(select(Proxy).where(Proxy.id == proxy_id))
    proxy = result.scalar_one_or_none()

    if not proxy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proxy {proxy_id} not found",
        )

    await db.delete(proxy)
    await db.commit()

    logger.info("Deleted proxy", proxy_id=proxy_id)


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_all_proxies(
    db: Annotated[AsyncSession, Depends(get_db)],
    confirm: bool = False,
):
    """Delete all proxies from the pool. Requires confirm=true."""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add ?confirm=true to delete all proxies",
        )

    result = await db.execute(select(func.count(Proxy.id)))
    count = result.scalar() or 0

    await db.execute(Proxy.__table__.delete())
    await db.commit()

    logger.info("Deleted all proxies", count=count)
    return {"deleted": count}
