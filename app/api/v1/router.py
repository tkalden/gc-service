"""
Main API router for v1
"""

from fastapi import APIRouter
from app.api.v1.auth.router import router as auth_router
from app.api.v1.clothes.router import router as clothes_router
from app.api.v1.outfits.router import router as outfits_router
from app.api.v1.avatar.router import router as avatar_router
from app.api.v1.upload.router import router as upload_router
from app.api.v1.admin.router import router as admin_router

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(clothes_router, prefix="/clothes", tags=["Clothing Items"])
api_router.include_router(outfits_router, prefix="/outfits", tags=["Outfits"])
api_router.include_router(avatar_router, prefix="/avatar", tags=["Avatar"])
api_router.include_router(upload_router, prefix="/upload", tags=["File Upload"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
