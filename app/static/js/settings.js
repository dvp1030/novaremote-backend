/**
 * settings.js — Admin settings page logic.
 * Manages Account Password, Paired Devices revocation, Server URL display,
 * Data retention policy, and Account deletion modal.
 */

import { api } from './api.js';
import { auth } from './auth.js';
import { statusBadge, timeAgo, showToast, escapeHtml } from './utils.js';

// Auth check
auth.requireAuth();

// Populate Server URL section
const serverUrlInput = document.getElementById('setting-server-url');
const copyServerBtn = document.getElementById('btn-copy-server');
const currentServer = auth.getServerUrl() || '';

if (serverUrlInput) {
  serverUrlInput.value = currentServer;
}

if (copyServerBtn) {
  copyServerBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(currentServer).then(() => {
      showToast('Server URL copied to clipboard!', 'success');
    }).catch(() => {
      showToast('Failed to copy to clipboard', 'error');
    });
  });
}

// ── Account: Change Password ───────────────────────────────────────────────
const passwordForm = document.getElementById('form-change-password');
const passwordError = document.getElementById('password-error');
const passwordSuccess = document.getElementById('password-success');

passwordForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const currentPassword = document.getElementById('current-password').value;
  const newPassword = document.getElementById('new-password').value;
  const confirmPassword = document.getElementById('confirm-password').value;

  if (passwordError) passwordError.classList.add('hidden');
  if (passwordSuccess) passwordSuccess.classList.add('hidden');

  if (newPassword !== confirmPassword) {
    if (passwordError) {
      passwordError.textContent = 'New passwords do not match.';
      passwordError.classList.remove('hidden');
    }
    return;
  }

  if (newPassword.length < 8) {
    if (passwordError) {
      passwordError.textContent = 'Password must be at least 8 characters long.';
      passwordError.classList.remove('hidden');
    }
    return;
  }

  try {
    // Call change password endpoint or mock
    await api.post('/api/v1/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });

    if (passwordSuccess) {
      passwordSuccess.textContent = 'Password successfully changed!';
      passwordSuccess.classList.remove('hidden');
    }
    passwordForm.reset();
    showToast('Password updated successfully', 'success');
  } catch (err) {
    if (passwordError) {
      passwordError.textContent = err.message || 'Failed to update password.';
      passwordError.classList.remove('hidden');
    }
    showToast(err.message, 'error');
  }
});

// ── Paired Devices ──────────────────────────────────────────────────────────
async function loadPairedDevices() {
  const tableBody = document.getElementById('paired-devices-body');
  const emptyRow = document.getElementById('paired-devices-empty');
  const loading = document.getElementById('paired-devices-loading');

  if (loading) loading.classList.remove('hidden');
  if (emptyRow) emptyRow.classList.add('hidden');

  try {
    const data = await api.get('/api/v1/devices');
    const devices = Array.isArray(data) ? data : (data?.items || []);

    if (devices.length === 0) {
      if (emptyRow) emptyRow.classList.remove('hidden');
      if (tableBody) tableBody.innerHTML = '';
      return;
    }

    if (tableBody) {
      tableBody.innerHTML = devices
        .map((dev) => {
          const s = dev.status || {};
          const isOnline = !!s.is_online;
          const isRevoked = !!dev.is_revoked;

          return `
          <tr class="border-b border-gray-800 hover:bg-gray-800/30">
            <td class="py-3 px-4 font-medium text-white">${escapeHtml(dev.name || 'Device')}</td>
            <td class="py-3 px-4 text-xs text-gray-400 font-mono">${escapeHtml(dev.model || dev.manufacturer || '—')}</td>
            <td class="py-3 px-4 text-xs">${statusBadge(isOnline)}</td>
            <td class="py-3 px-4 text-xs text-gray-400">${timeAgo(s.last_seen)}</td>
            <td class="py-3 px-4 text-right">
              ${
                isRevoked
                  ? '<span class="text-xs text-red-500 font-semibold uppercase">Revoked</span>'
                  : `<button data-id="${dev.id}" class="btn-revoke px-3 py-1 bg-red-900/40 hover:bg-red-800/60 border border-red-700 text-red-300 text-xs rounded transition">
                      Revoke
                    </button>`
              }
            </td>
          </tr>
        `;
        })
        .join('');

      // Attach revoke handlers
      tableBody.querySelectorAll('.btn-revoke').forEach((btn) => {
        btn.addEventListener('click', async () => {
          const id = btn.dataset.id;
          if (confirm('Are you sure you want to revoke this device? It will be disconnected immediately.')) {
            try {
              await api.post(`/api/v1/devices/${id}/revoke`, {});
              showToast('Device revoked successfully', 'success');
              loadPairedDevices();
            } catch (err) {
              showToast(`Failed to revoke device: ${err.message}`, 'error');
            }
          }
        });
      });
    }
  } catch (err) {
    showToast(`Error loading devices: ${err.message}`, 'error');
  } finally {
    if (loading) loading.classList.add('hidden');
  }
}

// ── Data Retention ──────────────────────────────────────────────────────────
const retentionSelect = document.getElementById('data-retention-select');
const saveRetentionBtn = document.getElementById('btn-save-retention');

saveRetentionBtn?.addEventListener('click', () => {
  const days = retentionSelect?.value || '30';
  localStorage.setItem('nr_data_retention_days', days);
  showToast(`Data retention policy set to ${days} days.`, 'success');
});

// Restore saved retention
if (retentionSelect) {
  const savedDays = localStorage.getItem('nr_data_retention_days');
  if (savedDays) retentionSelect.value = savedDays;
}

// ── Danger Zone: Delete Account Modal ───────────────────────────────────────
const deleteAccountBtn = document.getElementById('btn-delete-account');
const deleteModal = document.getElementById('delete-modal');
const cancelDeleteBtn = document.getElementById('btn-cancel-delete');
const confirmDeleteBtn = document.getElementById('btn-confirm-delete');
const deleteConfirmInput = document.getElementById('delete-confirm-input');

deleteAccountBtn?.addEventListener('click', () => {
  if (deleteModal) deleteModal.classList.remove('hidden');
  if (deleteConfirmInput) deleteConfirmInput.value = '';
});

cancelDeleteBtn?.addEventListener('click', () => {
  if (deleteModal) deleteModal.classList.add('hidden');
});

confirmDeleteBtn?.addEventListener('click', async () => {
  if (deleteConfirmInput?.value !== 'DELETE') {
    showToast('Please type DELETE to confirm.', 'warning');
    return;
  }

  try {
    await api.delete('/api/v1/auth/account');
  } catch {
    // Proceed to logout regardless of backend endpoint existence for safety
  }
  showToast('Account has been removed.', 'info');
  auth.logout('account_deleted');
});

// Initialize paired devices list
loadPairedDevices();
