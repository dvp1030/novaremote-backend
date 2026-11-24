/**
 * dashboard.js — Main dashboard page logic.
 * Fetches the device list, renders stat cards and device grid,
 * and keeps everything live via WebSocket events.
 */

import { api } from './api.js';
import { auth } from './auth.js';
import { ws } from './websocket.js';
import { formatBytes, timeAgo, batteryBar, statusBadge, networkIcon, showToast, escapeHtml } from './utils.js';

// ── Bootstrap ────────────────────────────────────────────────────────────────

auth.requireAuth();

// Show logged-in username
const usernameEl = document.getElementById('nav-username');
if (usernameEl) usernameEl.textContent = auth.getUsername() || 'Admin';

// Logout button
document.getElementById('btn-logout')?.addEventListener('click', () => {
  auth.logout();
});

// ── State ────────────────────────────────────────────────────────────────────

let devices = []; // array of device objects from API

// ── Stat cards ───────────────────────────────────────────────────────────────

function updateStats() {
  const total = devices.length;
  const online = devices.filter((d) => d.status?.is_online).length;
  const offline = total - online;
  const batteryValues = devices
    .map((d) => d.status?.battery_level)
    .filter((v) => v !== null && v !== undefined && !isNaN(v));
  const avgBattery =
    batteryValues.length > 0
      ? Math.round(batteryValues.reduce((a, b) => a + b, 0) / batteryValues.length)
      : null;

  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };

  set('stat-total', total);
  set('stat-online', online);
  set('stat-offline', offline);
  set('stat-battery', avgBattery !== null ? `${avgBattery}%` : '—');
}

// ── Device cards ─────────────────────────────────────────────────────────────

function deviceCardHtml(device) {
  const s = device.status || {};
  const isOnline = !!s.is_online;
  const battery = s.battery_level ?? null;
  const network = s.network_type || 'offline';
  const lastSeen = s.last_seen ? timeAgo(s.last_seen) : 'Never';
  const storage = s.storage_available_gb != null
    ? formatBytes(s.storage_available_gb * 1024 * 1024 * 1024)
    : '—';

  return `
    <div class="device-card card" data-device-id="${escapeHtml(device.id)}">
      <div class="flex items-start justify-between mb-3">
        <div>
          <h3 class="font-semibold text-white text-base leading-tight">${escapeHtml(device.name || 'Unknown Device')}</h3>
          <p class="text-xs text-gray-400 mt-0.5">${escapeHtml(device.model || device.manufacturer || '')}</p>
        </div>
        <div class="device-badge">${statusBadge(isOnline)}</div>
      </div>

      <div class="mb-3">${batteryBar(battery)}</div>

      <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-400 mb-4">
        <div>Android <span class="text-white">${escapeHtml(device.android_version || '—')}</span></div>
        <div>${networkIcon(network)}</div>
        <div>Storage <span class="text-white">${storage}</span></div>
        <div>Seen <span class="text-white">${lastSeen}</span></div>
      </div>

      <a href="device.html?id=${encodeURIComponent(device.id)}"
         class="btn-primary w-full text-center text-sm block">
        Manage →
      </a>
    </div>
  `;
}

function renderDeviceGrid() {
  const grid = document.getElementById('device-grid');
  const empty = document.getElementById('empty-state');
  const loading = document.getElementById('grid-loading');

  if (!grid) return;

  if (loading) loading.classList.add('hidden');

  if (devices.length === 0) {
    grid.innerHTML = '';
    if (empty) empty.classList.remove('hidden');
    return;
  }

  if (empty) empty.classList.add('hidden');
  grid.innerHTML = devices.map(deviceCardHtml).join('');
}

// ── Load devices ─────────────────────────────────────────────────────────────

async function loadDevices() {
  const loading = document.getElementById('grid-loading');
  const errorEl = document.getElementById('grid-error');
  if (loading) loading.classList.remove('hidden');
  if (errorEl) errorEl.classList.add('hidden');

  try {
    const data = await api.get('/api/v1/devices');
    // API might return { items: [...] } or plain array
    devices = Array.isArray(data) ? data : (data?.items || []);
    updateStats();
    renderDeviceGrid();
  } catch (err) {
    if (loading) loading.classList.add('hidden');
    if (errorEl) {
      errorEl.textContent = `Failed to load devices: ${err.message}`;
      errorEl.classList.remove('hidden');
    }
    showToast(`Failed to load devices: ${err.message}`, 'error');
  }
}

// ── WebSocket live updates ────────────────────────────────────────────────────

function applyStatusUpdate(deviceId, status) {
  const idx = devices.findIndex((d) => d.id === deviceId);
  if (idx === -1) {
    // New device appeared — reload full list
    loadDevices();
    return;
  }

  // Merge status into local state
  devices[idx].status = { ...(devices[idx].status || {}), ...status };

  // Patch just this card in the DOM (no full re-render)
  const card = document.querySelector(`[data-device-id="${CSS.escape(deviceId)}"]`);
  if (card) {
    const badgeEl = card.querySelector('.device-badge');
    if (badgeEl) badgeEl.innerHTML = statusBadge(!!status.is_online);

    const batteryEl = card.querySelector('.battery-wrap');
    if (batteryEl) batteryEl.innerHTML = batteryBar(status.battery_level ?? devices[idx].status.battery_level);
  }

  updateStats();
}

document.addEventListener('device:status', (e) => {
  applyStatusUpdate(e.detail.deviceId, e.detail.status);
});
document.addEventListener('device:online', (e) => {
  applyStatusUpdate(e.detail.deviceId, { is_online: true });
});
document.addEventListener('device:offline', (e) => {
  applyStatusUpdate(e.detail.deviceId, { is_online: false });
});

// Connection indicator
const connDot = document.getElementById('ws-status-dot');
const connLabel = document.getElementById('ws-status-label');
document.addEventListener('ws:connected', () => {
  if (connDot) { connDot.classList.remove('bg-red-500', 'bg-yellow-500'); connDot.classList.add('bg-green-500'); }
  if (connLabel) connLabel.textContent = 'Live';
});
document.addEventListener('ws:disconnected', () => {
  if (connDot) { connDot.classList.remove('bg-green-500', 'bg-yellow-500'); connDot.classList.add('bg-yellow-500'); }
  if (connLabel) connLabel.textContent = 'Reconnecting…';
});

// ── Init ─────────────────────────────────────────────────────────────────────

loadDevices();
ws.connect();

// Refresh every 60 s as a safety net for missed WS events
setInterval(loadDevices, 60000);
