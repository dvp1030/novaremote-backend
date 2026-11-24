
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import MessageResponse
from app.schemas.token import RefreshRequest, Token
from app.schemas.user import UserCreate, UserOut
from app.security.rate_limiter import limiter
from app.services.auth_service import (
    authenticate_user,
    get_current_user,
    issue_token_pair,
    register_user,
    rotate_tokens,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginBody:
    """Simple body parser; using pydantic model directly."""
    pass


from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await register_user(db, data)
    return UserOut.model_validate(user)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await authenticate_user(db, data.email, data.password)
    tokens = issue_token_pair(user.id)
    return Token(**tokens)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
) -> MessageResponse:
    # Stateless JWT: client discards token; server-side blacklist is out-of-scope for Phase 1
    return MessageResponse(message="Logged out successfully")


@router.post("/refresh", response_model=Token)
async def refresh_tokens(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    tokens = await rotate_tokens(db, data.refresh_token)
    return Token(**tokens)
