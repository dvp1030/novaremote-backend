/**
 * websocket.js — Dashboard WebSocket client for the NovaRemote dashboard.
 *
 * Connects to ws(s)://<server>/api/v1/ws/dashboard?token=<jwt>
 * Auto-reconnects with exponential backoff (1 s → 60 s max).
 * Dispatches CustomEvents on the document:
 *   - 'device:status'  → detail: { deviceId, status }
 *   - 'device:online'  → detail: { deviceId }
 *   - 'device:offline' → detail: { deviceId }
 *   - 'ws:connected'   → detail: {}
 *   - 'ws:disconnected'→ detail: {}
 * Sends a ping every 20 s to keep the connection alive.
 */

import { auth } from './auth.js';

class DashboardWebSocket {
  constructor() {
    this._ws = null;
    this._reconnectDelay = 1000;
    this._maxDelay = 60000;
    this._pingInterval = null;
    this._reconnectTimer = null;
    this._intentionalClose = false;
    this._connected = false;
  }

  /** Start connecting. Safe to call multiple times. */
  connect() {
    if (this._ws && (this._ws.readyState === WebSocket.OPEN || this._ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    this._intentionalClose = false;
    this._open();
  }

  /** Close the connection permanently (no reconnect). */
  disconnect() {
    this._intentionalClose = true;
    this._clearTimers();
    if (this._ws) {
      this._ws.close(1000, 'Client closed');
      this._ws = null;
    }
    this._connected = false;
  }

  get connected() {
    return this._connected;
  }

  _open() {
    const serverUrl = auth.getServerUrl();
    const token = auth.getAccessToken();
    if (!serverUrl || !token) return;

    // Convert http(s) to ws(s)
    const wsBase = serverUrl.replace(/^http/, 'ws');
    const url = `${wsBase}/api/v1/ws/dashboard?token=${encodeURIComponent(token)}`;

    try {
      this._ws = new WebSocket(url);
    } catch (err) {
      console.warn('[WS] Failed to create WebSocket:', err);
      this._scheduleReconnect();
      return;
    }

    this._ws.addEventListener('open', () => {
      console.info('[WS] Connected');
      this._connected = true;
      this._reconnectDelay = 1000; // reset backoff
      this._startPing();
      document.dispatchEvent(new CustomEvent('ws:connected', { detail: {} }));
    });

    this._ws.addEventListener('message', (evt) => {
      this._handleMessage(evt.data);
    });

    this._ws.addEventListener('close', (evt) => {
      this._connected = false;
      this._clearPing();
      document.dispatchEvent(new CustomEvent('ws:disconnected', { detail: {} }));
      if (!this._intentionalClose) {
        console.warn(`[WS] Disconnected (code ${evt.code}), reconnecting in ${this._reconnectDelay}ms…`);
        this._scheduleReconnect();
      }
    });

    this._ws.addEventListener('error', (err) => {
      console.warn('[WS] Error:', err);
      // 'close' event fires immediately after, which handles reconnect
    });
  }

  _handleMessage(raw) {
    let msg;
    try {
      msg = JSON.parse(raw);
    } catch {
      return; // ignore malformed frames
    }

    switch (msg.type) {
      case 'device_status':
        document.dispatchEvent(
          new CustomEvent('device:status', {
            detail: { deviceId: msg.device_id, status: msg.data || msg },
          })
        );
        break;

      case 'device_online':
        document.dispatchEvent(
          new CustomEvent('device:online', { detail: { deviceId: msg.device_id } })
        );
        // Also fire status update so battery/stats refresh
        document.dispatchEvent(
          new CustomEvent('device:status', {
            detail: { deviceId: msg.device_id, status: { is_online: true, ...(msg.data || {}) } },
          })
        );
        break;

      case 'device_offline':
        document.dispatchEvent(
          new CustomEvent('device:offline', { detail: { deviceId: msg.device_id } })
        );
        document.dispatchEvent(
          new CustomEvent('device:status', {
            detail: { deviceId: msg.device_id, status: { is_online: false, ...(msg.data || {}) } },
          })
        );
        break;

      case 'pong':
        // Server acknowledged our ping — nothing to do
        break;

      default:
        // Forward unknown types as generic events for future extensibility
        document.dispatchEvent(
          new CustomEvent(`ws:${msg.type}`, { detail: msg })
        );
    }
  }

  _startPing() {
    this._clearPing();
    this._pingInterval = setInterval(() => {
      if (this._ws && this._ws.readyState === WebSocket.OPEN) {
        this._ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 20000);
  }

  _clearPing() {
    if (this._pingInterval) {
      clearInterval(this._pingInterval);
      this._pingInterval = null;
    }
  }

  _scheduleReconnect() {
    this._clearTimers();
    this._reconnectTimer = setTimeout(() => {
      this._reconnectDelay = Math.min(this._reconnectDelay * 2, this._maxDelay);
      this._open();
    }, this._reconnectDelay);
  }

  _clearTimers() {
    this._clearPing();
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer);
      this._reconnectTimer = null;
    }
  }
}

export const ws = new DashboardWebSocket();
