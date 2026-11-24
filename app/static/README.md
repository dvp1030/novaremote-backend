# NovaRemote Admin Dashboard (Phase 1)

Modern, dark-themed responsive web dashboard for NovaRemote Android fleet management, telemetry monitoring, and remote session orchestration.

---

## Architecture & Features

- **Zero-Build Architecture**: Uses vanilla ES Modules and Tailwind CSS via CDN. Works directly in modern browsers without Node/Webpack/Vite bundling steps.
- **Dark Premium Theme**: Designed with custom palette `#0a0f1e` (navy), `#111827` (card background), `#3b82f6` (primary blue), `#06b6d4` (cyan), and Inter typography.
- **Authentication & Security**:
  - `sessionStorage` token management with automatic token rotation via refresh token logic.
  - Transparent 401 retry handling with auto-logout on session expiration.
  - Dynamic backend URL targeting (works across any host/port).
- **Real-time Telemetry WebSocket**:
  - Auto-reconnecting WebSocket client with exponential backoff (1s → 60s) and 20s keep-alive ping frames.
  - Live device online/offline indicators and real-time battery / stats updates.
- **Device Control Center**:
  - Overview telemetry cards (hardware, battery, network, storage, uptime, install ID).
  - Feature placeholders for upcoming phases (Camera, Mic, Screen, Location, Files, Notifications).
  - Activity log audit table with pagination.
- **Admin Settings**:
  - Account password change.
  - Device pairing revocation.
  - Telemetry retention selection.
  - Account deletion confirmation modal.

---

## Directory Structure

```
dashboard/
├── index.html           # Admin login page
├── dashboard.html       # Fleet overview & live telemetry grid
├── device.html          # Individual device control center & audit logs
├── settings.html        # Admin settings & device revocation
├── README.md            # Documentation
├── css/
│   └── app.css          # Custom styling (badges, battery bars, dark theme scrollbars)
├── assets/
│   └── logo.svg         # NovaRemote vector SVG logo
└── js/
    ├── api.js           # Authenticated fetch wrapper with auto-refresh
    ├── websocket.js     # Real-time WebSocket connection manager
    ├── auth.js          # Session handling & login orchestration
    ├── dashboard.js     # Main dashboard state & live event handling
    ├── device.js        # Device detail, tab switching, and log pagination
    ├── settings.js      # Settings logic and device revocation
    └── utils.js         # Formatting utilities (formatBytes, timeAgo, batteryBar, etc.)
```

---

## Quick Start Guide

### 1. Start the FastAPI Backend
Ensure the NovaRemote backend is running on `http://localhost:8000`:
```bash
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Launch the Dashboard
Run a local static HTTP server in the `dashboard` directory:
```bash
cd dashboard
python -m http.server 8080
```
Then navigate to:
```
http://localhost:8080
```
*(Alternatively, you can open `index.html` directly in any modern browser).*

### 3. Log In to Dashboard
1. **Server URL**: Enter `http://localhost:8000` (or your remote backend address).
2. **Username**: Enter your admin username (e.g., `admin`).
3. **Password**: Enter your admin password.
4. Click **Sign In**.

### 4. How to Pair an Android Device
1. On the dashboard header, click **"Pair New Device"** (or use the button in the empty state).
2. Provide a friendly name (e.g., `Pixel 8 Pro`) and click **"Generate Code"**.
3. A 6-digit numeric pairing code (valid for 10 minutes) will be displayed.
4. In the NovaRemote Android companion application on the target phone, enter the server URL and the 6-digit code to pair.
5. Once paired, the device will appear on the dashboard grid in real time with live battery, status, and network telemetry.
