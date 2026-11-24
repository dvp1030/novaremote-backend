import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    android_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    app_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    install_id: Mapped[str] = mapped_column(
        String(64), unique=True, default=lambda: str(uuid.uuid4()), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    owner: Mapped["User"] = relationship("User", back_populates="devices")  # noqa: F821
    credentials: Mapped[Optional["DeviceCredentials"]] = relationship(
        "DeviceCredentials", back_populates="device", uselist=False, cascade="all, delete-orphan"
    )
    status: Mapped[Optional["DeviceStatus"]] = relationship(  # noqa: F821
        "DeviceStatus", back_populates="device", uselist=False, cascade="all, delete-orphan"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(  # noqa: F821
        "ActivityLog", back_populates="device", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(  # noqa: F821
        "AuditLog", back_populates="device"
    )


class DeviceCredentials(Base):
    __tablename__ = "device_credentials"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    device_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    api_key: Mapped[str] = mapped_column(String(1024), nullable=False)  # hashed
    pairing_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    pairing_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    device: Mapped["Device"] = relationship("Device", back_populates="credentials")
