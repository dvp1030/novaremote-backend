/**
 * utils.js — Shared helper functions for the NovaRemote dashboard.
 */

/**
 * Format a byte count into a human-readable string.
 * @param {number} bytes
 * @returns {string}  e.g. "1.2 GB"
 */
export function formatBytes(bytes) {
  if (bytes === null || bytes === undefined || isNaN(bytes)) return '—';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k));
  const idx = Math.min(i, sizes.length - 1);
  return `${(bytes / Math.pow(k, idx)).toFixed(1)} ${sizes[idx]}`;
}

/**
 * Return a human-readable relative time string.
 * @param {string|Date|null} isoString  ISO-8601 datetime or Date object
 * @returns {string}  e.g. "just now", "3 min ago", "2 hours ago"
 */
export function timeAgo(isoString) {
  if (!isoString) return 'Never';
  const date = isoString instanceof Date ? isoString : new Date(isoString);
  if (isNaN(date.getTime())) return 'Unknown';
  const diff = Math.floor((Date.now() - date.getTime()) / 1000); // seconds
  if (diff < 10) return 'just now';
  if (diff < 60) return `${diff} sec ago`;
  const mins = Math.floor(diff / 60);
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days !== 1 ? 's' : ''} ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months} month${months !== 1 ? 's' : ''} ago`;
  const years = Math.floor(months / 12);
  return `${years} year${years !== 1 ? 's' : ''} ago`;
}

/**
 * Render an HTML battery bar.
 * @param {number|null} pct  0-100
 * @returns {string}  HTML string
 */
export function batteryBar(pct) {
  if (pct === null || pct === undefined || isNaN(pct)) {
    return `<span class="text-gray-500 text-sm">—</span>`;
  }
  const clamped = Math.max(0, Math.min(100, pct));
  let color = '#10b981'; // green
  if (clamped <= 20) color = '#ef4444';
  else if (clamped <= 40) color = '#f59e0b';

  return `
    <div class="flex items-center gap-2">
      <div class="battery-shell">
        <div class="battery-fill" style="width:${clamped}%; background:${color};"></div>
      </div>
      <span class="text-sm font-medium" style="color:${color};">${Math.round(clamped)}%</span>
    </div>
  `;
}

/**
 * Render an online/offline status badge pill.
 * @param {boolean} isOnline
 * @returns {string}  HTML string
 */
export function statusBadge(isOnline) {
  if (isOnline) {
    return `<span class="badge badge-online"><span class="badge-dot"></span>Online</span>`;
  }
  return `<span class="badge badge-offline"><span class="badge-dot"></span>Offline</span>`;
}

/**
 * Render a network icon SVG inline string.
 * @param {'wifi'|'mobile'|'offline'|string} type
 * @returns {string}  HTML string
 */
export function networkIcon(type) {
  const t = (type || '').toLowerCase();
  if (t === 'wifi') {
    return `<svg class="inline w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01M2.457 9a16 16 0 0119.086 0M5.282 12.287a11.5 11.5 0 0113.436 0"/>
    </svg> <span class="text-xs text-cyan-400 ml-1">WiFi</span>`;
  }
  if (t === 'mobile' || t === 'cellular' || t === 'lte' || t === '5g' || t === '4g') {
    return `<svg class="inline w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2h-2M8 4H6a2 2 0 00-2 2v14a2 2 0 002 2h2M9 10h6M9 14h6M9 18h6"/>
    </svg> <span class="text-xs text-blue-400 ml-1">Mobile</span>`;
  }
  return `<svg class="inline w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
      d="M18.364 5.636a9 9 0 010 12.728M5.636 5.636a9 9 0 000 12.728M15.536 8.464a5 5 0 010 7.072M8.464 8.464a5 5 0 000 7.072M12 12h.01"/>
  </svg> <span class="text-xs text-gray-500 ml-1">Offline</span>`;
}

/**
 * Escape HTML special characters to prevent XSS.
 * @param {string} str
 * @returns {string}
 */
export function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Show a toast notification.
 * @param {string} message
 * @param {'success'|'error'|'info'|'warning'} type
 */
export function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container') || (() => {
    const el = document.createElement('div');
    el.id = 'toast-container';
    el.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2';
    document.body.appendChild(el);
    return el;
  })();

  const colors = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    warning: 'bg-yellow-500',
    info: 'bg-blue-600',
  };
  const toast = document.createElement('div');
  toast.className = `toast-item ${colors[type] || colors.info} text-white px-4 py-3 rounded-lg shadow-lg text-sm flex items-center gap-2 max-w-xs`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => toast.classList.add('toast-visible'));

  setTimeout(() => {
    toast.classList.remove('toast-visible');
    toast.addEventListener('transitionend', () => toast.remove());
  }, 3500);
}
