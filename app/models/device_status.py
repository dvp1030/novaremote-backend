import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DeviceStatus(Base):
    __tablename__ = "device_status"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    device_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    battery_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_charging: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    network_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    wifi_ssid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    storage_available_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    uptime_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    device: Mapped["Device"] = relationship("Device", back_populates="status")  # noqa: F821
