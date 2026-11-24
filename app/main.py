
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import create_all_tables
from app.routers import (
    auth_router,
    devices_router,
    heartbeat_router,
    status_router,
    websocket_router,
)
from app.security.rate_limiter import limiter

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Lifespan startup: create database tables if they do not exist
    await create_all_tables()
    yield
    # Lifespan shutdown: cleanup if needed


app = FastAPI(
    title="NovaRemote Backend API",
    description="Backend API and WebSocket service for NovaRemote device management and telemetry.",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(status_router)
app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(heartbeat_router)
app.include_router(websocket_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "NovaRemote Backend"}
