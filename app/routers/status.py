
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["status"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
