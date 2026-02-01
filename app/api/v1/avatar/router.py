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
        logger.info(f"🎯 [Router] Try-on request received: avatar_id={request.avatar_id}, clothing_id={request.clothing_item_id}, user_id={current_user_id}")
        
        result = await avatar_service.perform_virtual_try_on(
            request, current_user_id
        )
        
        logger.info(f"🎯 [Router] Try-on completed successfully, result keys: {list(result.keys()) if result else 'None'}")
        
        return {
            "success": True,
            "data": result,
            "message": "Try-on preview generated successfully"
        }
    except Exception as e:
        logger.error(f"❌ [Router] Error performing virtual try-on: {str(e)}")
        import traceback
        logger.error(f"❌ [Router] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{avatar_id}", response_model=AvatarResponse)
async def get_avatar_by_id(avatar_id: str, current_user_id: str = Depends(get_current_user_id)):
    """Get avatar by ID (must belong to current user)"""
    try:
        from app.services.database_service import DatabaseService
        avatar = await DatabaseService.get_avatar_by_id(avatar_id)
        
        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar not found")
        
        # Ensure avatar belongs to current user
        if avatar.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return AvatarResponse(
            success=True,
            data=avatar,
            message="Avatar retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting avatar by ID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/try-on/history")
async def get_tryon_history(
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get user's virtual try-on history"""
    try:
        from app.services.database_service import DatabaseService
        results = await DatabaseService.get_user_tryon_results(current_user_id, limit)
        
        return {
            "success": True,
            "data": results,
            "count": len(results),
            "message": f"Retrieved {len(results)} try-on results"
        }
    except Exception as e:
        logger.error(f"Error getting try-on history: {str(e)}")
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
