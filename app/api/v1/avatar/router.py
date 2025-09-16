"""
Avatar router
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.core.logging import get_logger
from app.core.exceptions import ServiceUnavailableException
from app.services.avatar_service import avatar_service
from app.models.models import AvatarResponse, TryOnRequest
from app.middleware.middleware import get_current_user_id

logger = get_logger(__name__)
router = APIRouter()


@router.post("/upload", response_model=AvatarResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """Upload and process user avatar for digital twin creation"""
    try:
        if not avatar_service.is_available():
            raise ServiceUnavailableException(
                "Avatar service not available. Please install MediaPipe: pip install mediapipe"
            )
        
        # Process avatar upload
        result = await avatar_service.process_avatar_upload(file, current_user_id)
        
        return AvatarResponse(
            success=True,
            data=result["avatar"],
            message=f"Avatar created successfully with quality score: {result['quality_score']:.2f}"
        )
    except ServiceUnavailableException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=AvatarResponse)
async def get_user_avatar(current_user_id: str = Depends(get_current_user_id)):
    """Get user's current avatar"""
    try:
        from app.services.database_service import DatabaseService
        avatar = await DatabaseService.get_user_avatar(current_user_id)
        
        if not avatar:
            raise HTTPException(status_code=404, detail="No avatar found for user")
        
        return AvatarResponse(
            success=True,
            data=avatar,
            message="Avatar retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/try-on")
async def virtual_try_on(
    request: TryOnRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """Perform virtual try-on preview with user's avatar and clothing item"""
    try:
        result = await avatar_service.perform_virtual_try_on(
            request, current_user_id
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Try-on preview generated successfully"
        }
    except Exception as e:
        logger.error(f"Error performing virtual try-on: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/service/status")
async def get_avatar_service_status():
    """Get avatar service status and capabilities"""
    try:
        status = avatar_service.get_service_status()
        
        return {
            "success": True,
            "data": status,
            "message": "Avatar service status retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting avatar service status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
