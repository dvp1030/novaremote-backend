from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "Password123!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: dict):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user["email"],
            "username": "different_username",
            "password": "Password123!",
        },
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, test_user: dict):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "unique@example.com",
            "username": test_user["username"],
            "password": "Password123!",
        },
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "username": "bob",
            "password": "123",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: dict):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["plain_password"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: dict):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": "WrongPassword!",
        },
    )
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nobody@example.com",
            "password": "Password123!",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, test_user: dict):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["plain_password"],
        },
    )
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_token_with_invalid_token(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.jwt.token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_with_access_token_rejected(client: AsyncClient, test_user: dict):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["plain_password"],
        },
    )
    access_token = login_resp.json()["access_token"]

    # Passing access token as refresh token should be rejected
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert refresh_resp.status_code == 401
    assert "Wrong token type" in refresh_resp.json()["detail"]


@pytest.mark.asyncio
async def test_logout_endpoint(client: AsyncClient):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully"
