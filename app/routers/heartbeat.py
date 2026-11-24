
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.schemas.device_status import DeviceStatusOut, HeartbeatIn
from app.services.device_service import authenticate_device_by_api_key
from app.services.heartbeat_service import process_heartbeat
from app.websocket.manager import manager

router = APIRouter(prefix="/api/v1/devices", tags=["heartbeat"])


@router.post("/{device_id}/heartbeat", response_model=DeviceStatusOut)
async def heartbeat(
    device_id: str,
    data: HeartbeatIn,
    x_api_key: Annotated[str, Header(alias="X-API-Key")],
    db: AsyncSession = Depends(get_db),
) -> DeviceStatusOut:
    device = await authenticate_device_by_api_key(db, device_id, x_api_key)
    ds = await process_heartbeat(db, device, data)

    # Broadcast status update to dashboard WebSocket clients
    await manager.broadcast_to_dashboards(
        {
            "event": "device_status",
            "device_id": device_id,
            "battery_level": ds.battery_level,
            "is_charging": ds.is_charging,
            "network_type": ds.network_type,
            "wifi_ssid": ds.wifi_ssid,
            "storage_available_gb": ds.storage_available_gb,
            "uptime_seconds": ds.uptime_seconds,
            "is_online": ds.is_online,
        }
    )

    return DeviceStatusOut.model_validate(ds)
