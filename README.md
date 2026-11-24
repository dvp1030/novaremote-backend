# NovaRemote — Backend Service (Phase 1)

FastAPI-powered backend and WebSocket server for the NovaRemote device management and telemetry ecosystem.

---

## Features

- **Authentication & Security**:
  - JWT token pairs (`access` token 30 min, `refresh` token 7 days)
  - Argon2id password hashing via `argon2-cffi`
  - Per-IP rate limiting via `SlowAPI` on sensitive endpoints
  - Distinct token claim validation (`type: access | refresh | device`)
- **Device Management**:
  - Device registration with 6-digit numeric pairing codes (10-minute TTL)
  - Raw API key issuance (stored hashed in database)
  - Device listing, status inspection, revocation, and deletion
  - Device-level activity logging retrieval
- **Heartbeat & Telemetry**:
  - Authenticated device heartbeat endpoint (`POST /api/v1/devices/{id}/heartbeat` via `X-API-Key`)
  - Real-time DB status updates (battery level, charging status, network type, wifi SSID, storage, uptime, last_seen)
- **Real-time WebSockets**:
  - `/api/v1/ws/device/{device_id}?token=<device_jwt>`: Device bi-directional channel (pings, status updates, commands)
  - `/api/v1/ws/dashboard?token=<user_jwt>`: Broadcast channel streaming device status changes and online/offline presence
- **Storage & Migrations**:
  - Async SQLAlchemy 2.0 with `aiosqlite` (SQLite dev / local)
  - Alembic async migration suite (`migrations/`)

---

## Directory Structure

```
backend/
├── app/
│   ├── config.py              # Pydantic Settings & environment config
│   ├── database.py            # Async engine, sessionmaker, lifespan table creation
│   ├── main.py                # FastAPI app initialization, CORS, SlowAPI rate-limiting
│   ├── models/                # SQLAlchemy ORM models (UUID primary keys)
│   │   ├── user.py            # User model
│   │   ├── device.py          # Device and DeviceCredentials models
│   │   ├── device_status.py   # DeviceStatus model
│   │   └── audit.py           # AuditLog and ActivityLog models
│   ├── schemas/               # Pydantic v2 schemas for request/response serialization
│   │   ├── user.py
│   │   ├── device.py
│   │   ├── device_status.py
│   │   ├── token.py
│   │   └── common.py
│   ├── routers/               # APIRouters
│   │   ├── auth.py            # /api/v1/auth (register, login, logout, refresh)
│   │   ├── devices.py         # /api/v1/devices (register, list, get, delete, revoke, logs)
│   │   ├── heartbeat.py       # /api/v1/devices/{id}/heartbeat
│   │   ├── status.py          # /api/v1/health
│   │   └── websocket.py       # /api/v1/ws (device and dashboard websockets)
│   ├── services/              # Business logic & repository access
│   │   ├── auth_service.py
│   │   ├── device_service.py
│   │   └── heartbeat_service.py
│   ├── security/              # Cryptographic utilities & limits
│   │   ├── jwt_handler.py     # Token generation & claim decoding
│   │   ├── password.py        # Argon2 hashing and verification
│   │   └── rate_limiter.py    # SlowAPI instance
│   ├── websocket/             # WebSocket connection management
│   │   ├── manager.py         # In-memory connection registry & broadcast logic
│   │   └── auth.py            # WebSocket ticket & query token validation
│   ├── device_manager/
│   │   └── registry.py        # Active device in-memory query helpers
│   └── logging/
│       └── audit.py           # Async audit log helper
├── migrations/                # Alembic migration scripts
│   ├── env.py
│   └── versions/
│       └── 001_initial.py
├── tests/                     # Pytest suite with real assertions
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_devices.py
│   ├── test_heartbeat.py
│   └── test_websocket.py
├── alembic.ini
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (Python 3.11 recommended)
- `pip` or `uv`

### 2. Environment Setup

```bash
cd backend
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
```

### 3. Database Migrations

```bash
# Apply migrations to create the database schema:
alembic upgrade head
```

### 4. Running the Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Docs (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## API Summary

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new user account | No |
| `POST` | `/api/v1/auth/login` | Authenticate with credentials (rate limited) | No |
| `POST` | `/api/v1/auth/logout` | Client logout | No |
| `POST` | `/api/v1/auth/refresh` | Rotate access & refresh token pair | No (Refresh token body) |
| `GET` | `/api/v1/devices/` | List user's paired devices with status | Bearer JWT |
| `POST` | `/api/v1/devices/register` | Register device, get pairing code & API key | Bearer JWT |
| `GET` | `/api/v1/devices/{id}` | Device detail inspection | Bearer JWT |
| `DELETE`| `/api/v1/devices/{id}` | Remove device | Bearer JWT |
| `POST` | `/api/v1/devices/{id}/revoke`| Revoke device access credentials | Bearer JWT |
| `GET` | `/api/v1/devices/{id}/logs` | Retrieve device activity audit logs | Bearer JWT |
| `POST` | `/api/v1/devices/{id}/heartbeat` | Push device telemetry | `X-API-Key` |
| `WS` | `/api/v1/ws/device/{id}` | Bi-directional device WebSocket | `?token=<device_jwt>` |
| `WS` | `/api/v1/ws/dashboard` | Dashboard WebSocket streaming events | `?token=<access_jwt>` |

---

## Running Tests

Run the complete automated test suite with `pytest`:

```bash
pytest -v
```

All tests execute against an isolated in-memory SQLite database without altering the local development database.

---

## Running with Docker

```bash
docker build -t novaremote-backend:latest .
docker run -d -p 8000:8000 --name novaremote novaremote-backend:latest
```

---

## Phase 1 Deliberate Simplifications

1. **In-Memory WebSocket Registry**: Connection tracking is managed via an in-memory dictionary. For multi-node deployments in future phases, this can be swapped with Redis Pub/Sub.
2. **Stateless JWT Blacklist**: Refresh tokens rotate upon consumption. Active access tokens expire within 30 minutes; instant token revocation via Redis blocklist can be added in Phase 2.
3. **SQLite Development Database**: Uses SQLite via `aiosqlite` for zero-configuration local development. Production deployments switch `DATABASE_URL` to PostgreSQL with `asyncpg` without code modifications.
