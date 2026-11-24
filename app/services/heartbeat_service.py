
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.device_status import DeviceStatus
from app.schemas.device_status import HeartbeatIn


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def process_heartbeat(
    db: AsyncSession, device: Device, data: HeartbeatIn
) -> DeviceStatus:
    """Update or create DeviceStatus for a heartbeat."""
    result = await db.execute(
        select(DeviceStatus).where(DeviceStatus.device_id == device.id)
    )
    ds = result.scalar_one_or_none()
    if ds is None:
        ds = DeviceStatus(
            id=str(uuid.uuid4()),
            device_id=device.id,
        )
        db.add(ds)

    if data.battery_level is not None:
        ds.battery_level = data.battery_level
    if data.is_charging is not None:
        ds.is_charging = data.is_charging
    if data.network_type is not None:
        ds.network_type = data.network_type
    if data.wifi_ssid is not None:
        ds.wifi_ssid = data.wifi_ssid
    if data.storage_available_gb is not None:
        ds.storage_available_gb = data.storage_available_gb
    if data.uptime_seconds is not None:
        ds.uptime_seconds = data.uptime_seconds
    ds.last_seen = _utc_now()
    ds.is_online = True

    await db.flush()
    return ds
