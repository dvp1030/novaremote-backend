
from datetime import datetime

from pydantic import BaseModel

from app.schemas.device_status import DeviceStatusOut


class DeviceCreate(BaseModel):
    name: str
    model: str | None = None
    manufacturer: str | None = None
    android_version: str | None = None
    app_version: str | None = None


class DeviceOut(BaseModel):
    id: str
    owner_id: str
    name: str
    model: str | None
    manufacturer: str | None
    android_version: str | None
    app_version: str | None
    install_id: str
    is_active: bool
    is_revoked: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceRegistrationOut(BaseModel):
    device: DeviceOut
    pairing_code: str
    pairing_code_expires_at: datetime
    api_key: str  # raw key returned only at registration time


class DeviceDetail(BaseModel):
    id: str
    owner_id: str
    name: str
    model: str | None
    manufacturer: str | None
    android_version: str | None
    app_version: str | None
    install_id: str
    is_active: bool
    is_revoked: bool
    created_at: datetime
    updated_at: datetime
    status: DeviceStatusOut | None = None

    model_config = {"from_attributes": True}


class ActivityLogOut(BaseModel):
    id: str
    device_id: str
    event_type: str
    payload: dict | list | str | int | float | bool | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

