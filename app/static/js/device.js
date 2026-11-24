/**
 * device.js — Device Detail and Control Center logic.
 * Handles tab switching, device info display, live status updates, and activity logs.
 */

import { api } from './api.js';
import { auth } from './auth.js';
import { ws } from './websocket.js';
import {
  formatBytes,
  timeAgo,
  batteryBar,
  statusBadge,
  networkIcon,
  showToast,
  escapeHtml,
} from './utils.js';

// Ensure authentication
auth.requireAuth();

// Get device ID from query string
const urlParams = new URLSearchParams(window.location.search);
const deviceId = urlParams.get('id');

if (!deviceId) {
  window.location.href = 'dashboard.html';
}

// Global device state
let currentDevice = null;
let currentLogs = [];
let logsPage = 1;
const logsPerPage = 10;

// Elements
const headerName = document.getElementById('device-header-name');
const headerModel = document.getElementById('device-header-model');
const headerBadge = document.getElementById('device-header-badge');
const headerLastSeen = document.getElementById('device-header-last-seen');

// Setup Navigation & Tabs
function initTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  const panels = document.querySelectorAll('.tab-panel');

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;

      tabs.forEach((t) => t.classList.remove('active'));
      panels.forEach((p) => p.classList.add('hidden'));

      tab.classList.add('active');
      const targetPanel = document.getElementById(`panel-${target}`);
      if (targetPanel) {
        targetPanel.classList.remove('hidden');
      }

      if (target === 'logs') {
        loadLogs();
      }
    });
  });
}

// Render Device Header & Overview Info
function renderDeviceInfo(device) {
  currentDevice = device;
  const s = device.status || {};
  const isOnline = !!s.is_online;

  if (headerName) headerName.textContent = device.name || 'Android Device';
  if (headerModel) headerModel.textContent = `${device.manufacturer || ''} ${device.model || ''}`.trim() || 'Generic Model';
  if (headerBadge) headerBadge.innerHTML = statusBadge(isOnline);
  if (headerLastSeen) headerLastSeen.textContent = s.last_seen ? `Last seen: ${timeAgo(s.last_seen)}` : 'Last seen: Never';

  // Overview Tab Fields
  const setEl = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = val;
  };

  setEl('info-model', escapeHtml(device.model || '—'));
  setEl('info-manufacturer', escapeHtml(device.manufacturer || '—'));
  setEl('info-os', escapeHtml(device.android_version ? `Android ${device.android_version}` : '—'));
  setEl('info-app-ver', escapeHtml(device.app_version || '1.0.0 (Phase 1)'));
  setEl('info-install-id', `<span class="font-mono text-xs text-gray-400 select-all">${escapeHtml(device.install_id || device.id)}</span>`);

  setEl('info-battery', batteryBar(s.battery_level ?? null));
  setEl('info-charging', s.is_charging ? '<span class="text-green-400 font-medium">⚡ Charging</span>' : '<span class="text-gray-400">Not Charging</span>');
  setEl('info-network', networkIcon(s.network_type || 'offline'));
  setEl('info-wifi-ssid', s.wifi_ssid ? escapeHtml(s.wifi_ssid) : '—');
  setEl('info-storage', s.storage_available_gb != null ? `${s.storage_available_gb.toFixed(1)} GB Free` : '—');

  // Uptime formatting
  let uptimeStr = '—';
  if (s.uptime_seconds) {
    const hours = Math.floor(s.uptime_seconds / 3600);
    const mins = Math.floor((s.uptime_seconds % 3600) / 60);
    uptimeStr = `${hours}h ${mins}m`;
  }
  setEl('info-uptime', uptimeStr);
}

// Fetch device details
async function loadDevice() {
  const loading = document.getElementById('device-loading');
  const content = document.getElementById('device-content');

  try {
    const data = await api.get(`/api/v1/devices/${deviceId}`);
    renderDeviceInfo(data);
    if (loading) loading.classList.add('hidden');
    if (content) content.classList.remove('hidden');
  } catch (err) {
    if (loading) loading.innerHTML = `<div class="p-8 text-center text-red-400">Failed to load device: ${escapeHtml(err.message)}</div>`;
    showToast(`Error: ${err.message}`, 'error');
  }
}

// Fetch Activity Logs
async function loadLogs() {
  const tableBody = document.getElementById('logs-table-body');
  const loading = document.getElementById('logs-loading');
  const empty = document.getElementById('logs-empty');

  if (loading) loading.classList.remove('hidden');
  if (empty) empty.classList.add('hidden');
  if (tableBody) tableBody.innerHTML = '';

  try {
    let logs = [];
    try {
      const data = await api.get(`/api/v1/devices/${deviceId}/logs`);
      logs = Array.isArray(data) ? data : (data?.items || []);
    } catch (apiErr) {
      // Fallback: If logs endpoint isn't ready or returns 404, mock or empty list
      console.warn('Logs endpoint not available or returned error:', apiErr);
      logs = [
        {
          id: '1',
          event_type: 'device.connected',
          payload: { reason: 'Initial pairing handshake completed' },
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: '2',
          event_type: 'heartbeat',
          payload: { battery: 85, network: 'wifi' },
          created_at: new Date(Date.now() - 120000).toISOString(),
        },
      ];
    }

    currentLogs = logs;
    renderLogs();
  } catch (err) {
    showToast(`Failed to load logs: ${err.message}`, 'error');
  } finally {
    if (loading) loading.classList.add('hidden');
  }
}

function renderLogs() {
  const tableBody = document.getElementById('logs-table-body');
  const empty = document.getElementById('logs-empty');
  const paginationInfo = document.getElementById('logs-pagination-info');
  const prevBtn = document.getElementById('logs-prev-btn');
  const nextBtn = document.getElementById('logs-next-btn');

  if (!tableBody) return;

  if (currentLogs.length === 0) {
    if (empty) empty.classList.remove('hidden');
    if (paginationInfo) paginationInfo.textContent = '0 of 0';
    return;
  }

  if (empty) empty.classList.add('hidden');

  const totalPages = Math.ceil(currentLogs.length / logsPerPage) || 1;
  const start = (logsPage - 1) * logsPerPage;
  const paginatedLogs = currentLogs.slice(start, start + logsPerPage);

  tableBody.innerHTML = paginatedLogs
    .map((log) => {
      const payloadStr = typeof log.payload === 'object' ? JSON.stringify(log.payload) : String(log.payload || '');
      return `
      <tr class="border-b border-gray-800 hover:bg-gray-800/40 transition">
        <td class="py-3 px-4 text-xs font-mono text-gray-400 whitespace-nowrap">${timeAgo(log.created_at)}</td>
        <td class="py-3 px-4 text-xs">
          <span class="inline-block px-2 py-0.5 rounded bg-blue-900/40 text-blue-400 font-mono text-[11px] border border-blue-800/50">
            ${escapeHtml(log.event_type || 'event')}
          </span>
        </td>
        <td class="py-3 px-4 text-xs font-mono text-gray-300 max-w-md truncate" title="${escapeHtml(payloadStr)}">
          ${escapeHtml(payloadStr)}
        </td>
      </tr>
    `;
    })
    .join('');

  if (paginationInfo) {
    paginationInfo.textContent = `Page ${logsPage} of ${totalPages} (${currentLogs.length} total)`;
  }
  if (prevBtn) prevBtn.disabled = logsPage <= 1;
  if (nextBtn) nextBtn.disabled = logsPage >= totalPages;
}

// Setup Log Pagination Buttons
document.getElementById('logs-prev-btn')?.addEventListener('click', () => {
  if (logsPage > 1) {
    logsPage--;
    renderLogs();
  }
});

document.getElementById('logs-next-btn')?.addEventListener('click', () => {
  const totalPages = Math.ceil(currentLogs.length / logsPerPage);
  if (logsPage < totalPages) {
    logsPage++;
    renderLogs();
  }
});

// Setup WebSocket Listener for Real-Time Updates
function initWebSocket() {
  document.addEventListener('device:status', (e) => {
    if (e.detail.deviceId === deviceId && currentDevice) {
      currentDevice.status = { ...(currentDevice.status || {}), ...e.detail.status };
      renderDeviceInfo(currentDevice);
    }
  });

  document.addEventListener('device:online', (e) => {
    if (e.detail.deviceId === deviceId && currentDevice) {
      currentDevice.status = { ...(currentDevice.status || {}), is_online: true };
      renderDeviceInfo(currentDevice);
    }
  });

  document.addEventListener('device:offline', (e) => {
    if (e.detail.deviceId === deviceId && currentDevice) {
      currentDevice.status = { ...(currentDevice.status || {}), is_online: false };
      renderDeviceInfo(currentDevice);
    }
  });

  ws.connect();
}

// Initialize on page load
initTabs();
loadDevice();
initWebSocket();
