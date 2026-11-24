
from fastapi import WebSocket, WebSocketException, status
from jose import JWTError

from app.security.jwt_handler import decode_token


async def ws_authenticate_user(ws: WebSocket) -> str:
    """
    Authenticate a WebSocket connection using ?token= query param.
    Returns user_id on success. Raises WebSocketException on failure.
    """
    token = ws.query_params.get("token")
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
    try:
        payload = decode_token(token)
    except JWTError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
    if payload.get("type") != "access":
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Wrong token type")
    sub = payload.get("sub")
    if not sub:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token subject")
    return str(sub)


async def ws_authenticate_device(ws: WebSocket) -> str:
    """
    Authenticate a device WebSocket connection using ?token= query param.
    Returns device_id on success.
    """
    token = ws.query_params.get("token")
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
    try:
        payload = decode_token(token)
    except JWTError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
    if payload.get("type") != "device":
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Wrong token type")
    sub = payload.get("sub")
    if not sub:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token subject")
    return str(sub)
