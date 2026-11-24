
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_audit(
    db: AsyncSession,
    action: str,
    user_id: str | None = None,
    device_id: str | None = None,
    details: Any = None,
    ip_address: str | None = None,
) -> None:
    """Write an audit log entry."""
    entry = AuditLog(
        user_id=user_id,
        device_id=device_id,
        action=action,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    # Caller is responsible for commit via get_db dependency
