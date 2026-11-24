from app.routers.auth import router as auth_router
from app.routers.devices import router as devices_router
from app.routers.heartbeat import router as heartbeat_router
from app.routers.status import router as status_router
from app.routers.websocket import router as websocket_router

__all__ = [
    "auth_router",
    "devices_router",
    "heartbeat_router",
    "status_router",
    "websocket_router",
]
