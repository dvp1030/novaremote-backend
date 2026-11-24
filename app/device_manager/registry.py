
"""
In-memory device registry that tracks which device IDs are currently connected
via WebSocket. The source of truth for is_online is the DeviceStatus table,
but this registry provides a fast in-memory view.
"""

from app.websocket.manager import manager


def is_device_online(device_id: str) -> bool:
    return manager.is_device_connected(device_id)


def connected_devices() -> list[str]:
    return manager.connected_device_ids()
