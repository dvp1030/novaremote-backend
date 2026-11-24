/**
 * api.js — Authenticated fetch wrapper for the NovaRemote dashboard.
 *
 * Features:
 *  - Reads server URL from sessionStorage.
 *  - Injects Authorization: Bearer <token> on every request.
 *  - On 401: attempts one token refresh, retries the original request.
 *  - On persistent 401 after refresh: redirects to login.
 *  - Returns parsed JSON or throws ApiError.
 */

import { auth } from './auth.js';

export class ApiError extends Error {
  constructor(message, status, body) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

class ApiClient {
  constructor() {
    this._refreshing = null; // singleton refresh promise
  }

  get baseUrl() {
    const url = auth.getServerUrl();
    if (!url) {
      auth.logout('no_server');
      throw new ApiError('No server URL configured.', 0, null);
    }
    return url;
  }

  /**
   * Core fetch with auth injection.
   * @param {string} path   e.g. "/api/v1/devices"
   * @param {RequestInit} options
   * @param {boolean} _retry  internal flag — do not set manually
   */
  async request(path, options = {}, _retry = false) {
    const token = auth.getAccessToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const url = `${this.baseUrl}${path}`;
    let res;
    try {
      res = await fetch(url, { ...options, headers });
    } catch (networkErr) {
      throw new ApiError(`Network error: ${networkErr.message}`, 0, null);
    }

    // 401 → attempt refresh once
    if (res.status === 401 && !_retry) {
      try {
        await this._refresh();
      } catch {
        auth.logout('session_expired');
        return; // unreachable after redirect
      }
      return this.request(path, options, true); // retry with new token
    }

    if (res.status === 401 && _retry) {
      auth.logout('session_expired');
      return; // unreachable
    }

    // Parse body
    const contentType = res.headers.get('content-type') || '';
    let body = null;
    if (contentType.includes('application/json')) {
      body = await res.json().catch(() => null);
    } else {
      body = await res.text().catch(() => null);
    }

    if (!res.ok) {
      const message =
        (body && (body.detail || body.message || body.error)) ||
        `HTTP ${res.status}`;
      throw new ApiError(message, res.status, body);
    }

    return body;
  }

  /** Singleton refresh — multiple concurrent 401s share one refresh call. */
  _refresh() {
    if (this._refreshing) return this._refreshing;
    this._refreshing = (async () => {
      const refreshToken = auth.getRefreshToken();
      if (!refreshToken) throw new Error('No refresh token');

      const res = await fetch(`${this.baseUrl}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) throw new Error('Refresh failed');
      const data = await res.json();
      auth.updateTokens({
        accessToken: data.access_token,
        refreshToken: data.refresh_token || refreshToken,
      });
    })().finally(() => {
      this._refreshing = null;
    });
    return this._refreshing;
  }

  // Convenience methods
  get(path, options = {}) {
    return this.request(path, { ...options, method: 'GET' });
  }

  post(path, body, options = {}) {
    return this.request(path, {
      ...options,
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  put(path, body, options = {}) {
    return this.request(path, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  patch(path, body, options = {}) {
    return this.request(path, {
      ...options,
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }

  delete(path, options = {}) {
    return this.request(path, { ...options, method: 'DELETE' });
  }
}

export const api = new ApiClient();
