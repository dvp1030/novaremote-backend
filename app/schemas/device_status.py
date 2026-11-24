
from datetime import datetime

from pydantic import BaseModel, Field


class DeviceStatusOut(BaseModel):
    device_id: str
    battery_level: int | None = None
    is_charging: bool | None = None
    network_type: str | None = None
    wifi_ssid: str | None = None
    storage_available_gb: float | None = None
    uptime_seconds: int | None = None
    last_seen: datetime | None = None
    is_online: bool = False

    model_config = {"from_attributes": True}


class HeartbeatIn(BaseModel):
    battery_level: int | None = Field(None, ge=0, le=100)
    is_charging: bool | None = None
    network_type: str | None = None
    wifi_ssid: str | None = None
    storage_available_gb: float | None = None
    uptime_seconds: int | None = None
