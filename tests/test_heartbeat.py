from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.fixture
async def registered_device(client: AsyncClient, auth_headers: dict) -> dict:
    resp = await client.post(
        "/api/v1/devices/register",
        json={"name": "Heartbeat Test Phone"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_heartbeat_success(client: AsyncClient, registered_device: dict):
    device_id = registered_device["device"]["id"]
    api_key = registered_device["api_key"]

    payload = {
        "battery_level": 85,
        "is_charging": True,
        "network_type": "WIFI",
        "wifi_ssid": "Home-Network",
        "storage_available_gb": 42.5,
        "uptime_seconds": 3600,
    }

    resp = await client.post(
        f"/api/v1/devices/{device_id}/heartbeat",
        json=payload,
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_id"] == device_id
    assert data["battery_level"] == 85
    assert data["is_charging"] is True
    assert data["network_type"] == "WIFI"
    assert data["wifi_ssid"] == "Home-Network"
    assert data["storage_available_gb"] == 42.5
    assert data["uptime_seconds"] == 3600
    assert data["is_online"] is True
    assert data["last_seen"] is not None


@pytest.mark.asyncio
async def test_heartbeat_invalid_api_key(client: AsyncClient, registered_device: dict):
    device_id = registered_device["device"]["id"]
    resp = await client.post(
        f"/api/v1/devices/{device_id}/heartbeat",
        json={"battery_level": 50},
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_heartbeat_missing_api_key(client: AsyncClient, registered_device: dict):
    device_id = registered_device["device"]["id"]
    resp = await client.post(
        f"/api/v1/devices/{device_id}/heartbeat",
        json={"battery_level": 50},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_heartbeat_revoked_device(
    client: AsyncClient, registered_device: dict, auth_headers: dict
):
    device_id = registered_device["device"]["id"]
    api_key = registered_device["api_key"]

    # Revoke device
    revoke_resp = await client.post(
        f"/api/v1/devices/{device_id}/revoke",
        headers=auth_headers,
    )
    assert revoke_resp.status_code == 200

    # Heartbeat must fail
    resp = await client.post(
        f"/api/v1/devices/{device_id}/heartbeat",
        json={"battery_level": 50},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 401
