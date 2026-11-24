
import random
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.device import Device, DeviceCredentials
from app.models.user import User
from app.schemas.device import DeviceCreate
from app.security.jwt_handler import create_device_token
from app.security.password import hash_password


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_pairing_code() -> str:
    return "".join(random.choices(string.digits, k=6))


def _generate_api_key() -> str:
    return secrets.token_urlsafe(32)


async def register_device(
    db: AsyncSession, owner: User, data: DeviceCreate
) -> tuple[Device, str, str]:
    """
    Create a device + credentials. Returns (device, raw_api_key, pairing_code).
    """
    device = Device(
        owner_id=owner.id,
        name=data.name,
        model=data.model,
        manufacturer=data.manufacturer,
        android_version=data.android_version,
        app_version=data.app_version,
    )
    db.add(device)
    await db.flush()

    raw_api_key = _generate_api_key()
    pairing_code = _generate_pairing_code()
    expires_at = _utc_now() + timedelta(minutes=10)

    creds = DeviceCredentials(
        device_id=device.id,
        api_key=hash_password(raw_api_key),
        pairing_code=pairing_code,
        pairing_code_expires_at=expires_at,
    )
    db.add(creds)
    await db.flush()
    return device, raw_api_key, pairing_code


async def list_devices(db: AsyncSession, owner_id: str) -> list[Device]:
    result = await db.execute(
        select(Device)
        .where(Device.owner_id == owner_id)
        .options(selectinload(Device.status))
        .order_by(Device.created_at.desc())
    )
    return list(result.scalars().all())


async def get_device(db: AsyncSession, device_id: str, owner_id: str) -> Device:
    result = await db.execute(
        select(Device)
        .where(Device.id == device_id, Device.owner_id == owner_id)
        .options(selectinload(Device.status))
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


async def delete_device(db: AsyncSession, device_id: str, owner_id: str) -> None:
    device = await get_device(db, device_id, owner_id)
    await db.delete(device)


async def revoke_device(db: AsyncSession, device_id: str, owner_id: str) -> Device:
    device = await get_device(db, device_id, owner_id)
    device.is_revoked = True
    device.is_active = False
    db.add(device)
    await db.flush()
    return device


async def authenticate_device_by_api_key(
    db: AsyncSession, device_id: str, raw_api_key: str
) -> Device:
    """Verify device API key. Returns Device or raises 401."""
    from app.security.password import verify_password  # local import avoids circular

    result = await db.execute(
        select(Device)
        .where(Device.id == device_id, Device.is_active == True, Device.is_revoked == False)
        .options(selectinload(Device.credentials))
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device not found or inactive")
    if device.credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device has no credentials")
    if not verify_password(raw_api_key, device.credentials.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return device
