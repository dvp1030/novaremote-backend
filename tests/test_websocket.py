from __future__ import annotations

import json
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.security.jwt_handler import create_access_token, create_device_token


def test_device_ws_missing_token():
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/device/some-device"):
            pass


def test_device_ws_invalid_token():
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/device/some-device?token=invalid.token"):
            pass


def test_device_ws_wrong_token_type():
    # User access token passed instead of device token
    access_token = create_access_token("some-device")
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/device/some-device?token={access_token}"):
            pass


def test_device_ws_device_id_mismatch():
    # Token is for device-1, but path is device-2
    token = create_device_token("device-1")
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/device/device-2?token={token}"):
            pass


def test_device_ws_ping_pong():
    device_id = "test-device-uuid"
    token = create_device_token(device_id)
    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/ws/device/{device_id}?token={token}") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        data = ws.receive_json()
        assert data == {"type": "pong"}


def test_dashboard_ws_missing_token():
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/dashboard"):
            pass


def test_dashboard_ws_connect_and_ping():
    user_id = "test-user-uuid"
    token = create_access_token(user_id)
    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/ws/dashboard?token={token}") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        data = ws.receive_json()
        assert data == {"type": "pong"}
