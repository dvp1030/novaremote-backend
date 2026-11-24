from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_device_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/api/v1/devices/register",
        json={"name": "Pixel 8 Pro"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_device_success(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/devices/register",
        json={
            "name": "Pixel 8 Pro",
            "model": "Pixel 8 Pro",
            "manufacturer": "Google",
            "android_version": "14",
            "app_version": "1.0.0",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "pairing_code" in data
    assert len(data["pairing_code"]) == 6
    assert "api_key" in data
    assert len(data["api_key"]) > 20
    assert data["device"]["name"] == "Pixel 8 Pro"
    assert data["device"]["is_active"] is True
    assert data["device"]["is_revoked"] is False


@pytest.mark.asyncio
async def test_list_devices(client: AsyncClient, auth_headers: dict):
    # Register two devices
    await client.post(
        "/api/v1/devices/register",
        json={"name": "Device 1"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/devices/register",
        json={"name": "Device 2"},
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/devices/", headers=auth_headers)
    assert resp.status_code == 200
    devices = resp.json()
    assert len(devices) >= 2
    device_names = [d["name"] for d in devices]
    assert "Device 1" in device_names
    assert "Device 2" in device_names


@pytest.mark.asyncio
async def test_get_device_detail(client: AsyncClient, auth_headers: dict):
    reg = await client.post(
        "/api/v1/devices/register",
        json={"name": "Samsung Galaxy S24"},
        headers=auth_headers,
    )
    device_id = reg.json()["device"]["id"]

    resp = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == device_id
    assert data["name"] == "Samsung Galaxy S24"


@pytest.mark.asyncio
async def test_get_device_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/devices/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_revoke_device(client: AsyncClient, auth_headers: dict):
    reg = await client.post(
        "/api/v1/devices/register",
        json={"name": "To Revoke"},
        headers=auth_headers,
    )
    device_id = reg.json()["device"]["id"]

    resp = await client.post(f"/api/v1/devices/{device_id}/revoke", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_revoked"] is True
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_device(client: AsyncClient, auth_headers: dict):
    reg = await client.post(
        "/api/v1/devices/register",
        json={"name": "To Delete"},
        headers=auth_headers,
    )
    device_id = reg.json()["device"]["id"]

    del_resp = await client.delete(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["message"] == "Device deleted"

    # Confirm it is gone
    get_resp = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_device_isolation_between_users(client: AsyncClient, auth_headers: dict):
    # Register device under user 1
    reg = await client.post(
        "/api/v1/devices/register",
        json={"name": "User 1 Device"},
        headers=auth_headers,
    )
    device_id = reg.json()["device"]["id"]

    # Register user 2 and log in
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user2@example.com",
            "username": "user2",
            "password": "Password123!",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "user2@example.com", "password": "Password123!"},
    )
    token2 = login_resp.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {token2}"}

    # User 2 cannot access user 1's device
    resp = await client.get(f"/api/v1/devices/{device_id}", headers=user2_headers)
    assert resp.status_code == 404
