
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device_status import DeviceStatus
from app.websocket.auth import ws_authenticate_device, ws_authenticate_user
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])


async def _mark_online(db: AsyncSession, device_id: str, is_online: bool) -> None:
    result = await db.execute(select(DeviceStatus).where(DeviceStatus.device_id == device_id))
    ds = result.scalar_one_or_none()
    if ds is not None:
        ds.is_online = is_online
        if is_online:
            ds.last_seen = datetime.now(timezone.utc)
        db.add(ds)
        await db.commit()


@router.websocket("/device/{device_id}")
async def device_ws(
    device_id: str,
    ws: WebSocket,
    db: AsyncSession = Depends(get_db),
) -> None:
    authenticated_device_id = await ws_authenticate_device(ws)
    if authenticated_device_id != device_id:
        await ws.close(code=1008, reason="Device ID mismatch")
        return

    await manager.connect_device(device_id, ws)
    await _mark_online(db, device_id, True)
    await manager.broadcast_to_dashboards({"event": "device_online", "device_id": device_id})

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"error": "Invalid JSON"})
                continue

            msg_type = msg.get("type")

            if msg_type == "ping":
                await ws.send_json({"type": "pong"})

            elif msg_type == "status_update":
                payload = msg.get("data", {})
                await manager.broadcast_to_dashboards(
                    {"event": "status_update", "device_id": device_id, "data": payload}
                )
                # Update DB status
                result = await db.execute(
                    select(DeviceStatus).where(DeviceStatus.device_id == device_id)
                )
                ds = result.scalar_one_or_none()
                if ds:
                    for field in [
                        "battery_level", "is_charging", "network_type",
                        "wifi_ssid", "storage_available_gb", "uptime_seconds"
                    ]:
                        if field in payload:
                            setattr(ds, field, payload[field])
                    ds.last_seen = datetime.now(timezone.utc)
                    ds.is_online = True
                    db.add(ds)
                    await db.commit()

            else:
                await ws.send_json({"error": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect_device(device_id)
        await _mark_online(db, device_id, False)
        await manager.broadcast_to_dashboards({"event": "device_offline", "device_id": device_id})


@router.websocket("/dashboard")
async def dashboard_ws(
    ws: WebSocket,
    db: AsyncSession = Depends(get_db),
) -> None:
    user_id = await ws_authenticate_user(ws)
    await manager.connect_dashboard(ws)
    logger.info("Dashboard WS authenticated for user %s", user_id)

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"error": "Invalid JSON"})
                continue

            if msg.get("type") == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect_dashboard(ws)
