
import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for devices and dashboard clients."""

    def __init__(self) -> None:
        # device_id -> WebSocket
        self._device_connections: dict[str, WebSocket] = {}
        # dashboard connections list
        self._dashboard_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    # --- Device connections ---

    async def connect_device(self, device_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            if device_id in self._device_connections:
                # Close old connection if device reconnects
                try:
                    old = self._device_connections[device_id]
                    await old.close(code=1001, reason="replaced")
                except Exception:
                    pass
            self._device_connections[device_id] = ws
        logger.info("Device %s connected", device_id)

    async def disconnect_device(self, device_id: str) -> None:
        async with self._lock:
            self._device_connections.pop(device_id, None)
        logger.info("Device %s disconnected", device_id)

    def is_device_connected(self, device_id: str) -> bool:
        return device_id in self._device_connections

    async def send_to_device(self, device_id: str, data: dict[str, Any]) -> bool:
        ws = self._device_connections.get(device_id)
        if ws is None:
            return False
        try:
            await ws.send_json(data)
            return True
        except Exception as exc:
            logger.warning("Failed to send to device %s: %s", device_id, exc)
            return False

    # --- Dashboard connections ---

    async def connect_dashboard(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._dashboard_connections.append(ws)
        logger.info("Dashboard client connected (%d total)", len(self._dashboard_connections))

    async def disconnect_dashboard(self, ws: WebSocket) -> None:
        async with self._lock:
            try:
                self._dashboard_connections.remove(ws)
            except ValueError:
                pass
        logger.info("Dashboard client disconnected (%d remaining)", len(self._dashboard_connections))

    async def broadcast_to_dashboards(self, data: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        payload = json.dumps(data)
        async with self._lock:
            targets = list(self._dashboard_connections)
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    try:
                        self._dashboard_connections.remove(ws)
                    except ValueError:
                        pass

    # --- Helpers ---

    def connected_device_ids(self) -> list[str]:
        return list(self._device_connections.keys())


manager = ConnectionManager()
