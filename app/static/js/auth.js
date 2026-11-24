/**
 * auth.js — Login, logout, and token storage for the NovaRemote dashboard.
 * Uses sessionStorage so credentials are cleared when the tab closes.
 */

const KEYS = {
  ACCESS_TOKEN: 'nr_access_token',
  REFRESH_TOKEN: 'nr_refresh_token',
  SERVER_URL: 'nr_server_url',
  USERNAME: 'nr_username',
};

export const auth = {
  /** Store tokens and server URL after a successful login. */
  saveSession({ accessToken, refreshToken, serverUrl, username }) {
    sessionStorage.setItem(KEYS.ACCESS_TOKEN, accessToken);
    sessionStorage.setItem(KEYS.REFRESH_TOKEN, refreshToken);
    sessionStorage.setItem(KEYS.SERVER_URL, serverUrl.replace(/\/+$/, ''));
    if (username) sessionStorage.setItem(KEYS.USERNAME, username);
  },

  getAccessToken() {
    return sessionStorage.getItem(KEYS.ACCESS_TOKEN);
  },

  getRefreshToken() {
    return sessionStorage.getItem(KEYS.REFRESH_TOKEN);
  },

  getServerUrl() {
    return sessionStorage.getItem(KEYS.SERVER_URL);
  },

  getUsername() {
    return sessionStorage.getItem(KEYS.USERNAME);
  },

  /** Update only the access token (after a refresh). */
  updateAccessToken(token) {
    sessionStorage.setItem(KEYS.ACCESS_TOKEN, token);
  },

  /** Update both tokens (after a refresh that rotates both). */
  updateTokens({ accessToken, refreshToken }) {
    sessionStorage.setItem(KEYS.ACCESS_TOKEN, accessToken);
    if (refreshToken) sessionStorage.setItem(KEYS.REFRESH_TOKEN, refreshToken);
  },

  /** Returns true if the user appears to be logged in. */
  isLoggedIn() {
    return !!(this.getAccessToken() && this.getServerUrl());
  },

  /** Clear all session data and redirect to login. */
  logout(reason = '') {
    sessionStorage.removeItem(KEYS.ACCESS_TOKEN);
    sessionStorage.removeItem(KEYS.REFRESH_TOKEN);
    // Keep server URL so the user does not have to re-type it on the next login
    const url = new URL('index.html', window.location.href);
    if (reason) url.searchParams.set('reason', reason);
    window.location.href = url.toString();
  },

  /**
   * Guard: redirect to login if not authenticated.
   * Call this at the top of every protected page.
   */
  requireAuth() {
    if (!this.isLoggedIn()) {
      this.logout('session_expired');
    }
  },
};

/**
 * Handle the login form on index.html.
 * This function is imported and called only from auth.js or index.html inline script.
 */
export async function handleLoginForm(formEl, errorEl, spinnerEl, buttonEl) {
  const serverUrl = formEl.querySelector('#server-url').value.trim().replace(/\/+$/, '');
  const username = formEl.querySelector('#username').value.trim();
  const password = formEl.querySelector('#password').value;

  if (!serverUrl || !username || !password) {
    errorEl.textContent = 'Please fill in all fields.';
    errorEl.classList.remove('hidden');
    return;
  }

  // Show loading state
  errorEl.classList.add('hidden');
  spinnerEl.classList.remove('hidden');
  buttonEl.disabled = true;

  try {
    const res = await fetch(`${serverUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `Login failed (${res.status})`);
    }

    const data = await res.json();

    auth.saveSession({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      serverUrl,
      username,
    });

    window.location.href = 'dashboard.html';
  } catch (err) {
    errorEl.textContent = err.message || 'Could not connect to server.';
    errorEl.classList.remove('hidden');
  } finally {
    spinnerEl.classList.add('hidden');
    buttonEl.disabled = false;
  }
}
