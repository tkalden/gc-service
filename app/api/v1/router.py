"""
Main API router for v1
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.clothes import router as clothes_router
from app.api.v1.outfits import router as outfits_router
from app.api.v1.avatar import router as avatar_router
from app.api.v1.upload import router as upload_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(clothes_router, prefix="/clothes", tags=["Clothing Items"])
api_router.include_router(outfits_router, prefix="/outfits", tags=["Outfits"])
api_router.include_router(avatar_router, prefix="/avatar", tags=["Avatar"])
api_router.include_router(upload_router, prefix="/upload", tags=["File Upload"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
