from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, items

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, tags=["authentication"])

# Include user management routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Include item management routes
api_router.include_router(items.router, prefix="/items", tags=["items"])
