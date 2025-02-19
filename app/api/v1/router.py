"""Base router configuration for API v1."""
from fastapi import APIRouter

# Create the main v1 router with prefix
router = APIRouter(prefix="/v1")

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}