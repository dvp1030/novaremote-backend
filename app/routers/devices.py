
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from sqlalchemy import select
from app.models.audit import ActivityLog
from app.schemas.device import ActivityLogOut, DeviceCreate, DeviceDetail, DeviceOut
from app.schemas.device import DeviceRegistrationOut
from app.services.auth_service import get_current_user
from app.services.device_service import (
    delete_device,
    get_device,
    list_devices,
    register_device,
    revoke_device,
)

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


async def _current_user(
    authorization: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    token = authorization[7:]
    return await get_current_user(db, token)


@router.post("/register", response_model=DeviceRegistrationOut, status_code=201)
async def register_device_endpoint(
    data: DeviceCreate,
    user: User = Depends(_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeviceRegistrationOut:
    device, raw_api_key, pairing_code = await register_device(db, user, data)
    return DeviceRegistrationOut(
        device=DeviceOut.model_validate(device),
        pairing_code=pairing_code,
        pairing_code_expires_at=device.credentials.pairing_code_expires_at,
        api_key=raw_api_key,
    )


@router.get("/", response_model=list[DeviceDetail])
async def list_devices_endpoint(
    user: User = Depends(_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DeviceDetail]:
    devices = await list_devices(db, user.id)
    return [DeviceDetail.model_validate(d) for d in devices]


@router.get("/{device_id}", response_model=DeviceDetail)
async def get_device_endpoint(
    device_id: str,
    user: User = Depends(_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeviceDetail:
    device = await get_device(db, device_id, user.id)
    return DeviceDetail.model_validate(device)


@router.delete("/{device_id}", response_model=MessageResponse)
async def delete_device_endpoint(
    device_id: str,
    user: User = Depends(_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await delete_device(db, device_id, user.id)
    return MessageResponse(message="Device deleted")


@router.post("/{device_id}/revoke", response_model=DeviceOut)
async def revoke_device_endpoint(
    device_id: str,
    user: User = Depends(_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeviceOut:
    device = await revoke_device(db, device_id, user.id)
    return DeviceOut.model_validate(device)


@router.get("/{device_id}/logs", response_model=list[ActivityLogOut])
async def get_device_logs_endpoint(
    device_id: str,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ActivityLogOut]:
    # Ensure device belongs to current user
    await get_device(db, device_id, user.id)
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.device_id == device_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs = result.scalars().all()
    return [ActivityLogOut.model_validate(log) for log in logs]

