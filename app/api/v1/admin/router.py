"""
Admin router
"""

from fastapi import APIRouter, Depends, HTTPException
from app.core.logging import get_logger
from app.core.exceptions import ServiceUnavailableException
from app.services.background_removal import background_removal_service
from app.middleware.auth import get_current_user_id

logger = get_logger(__name__)
router = APIRouter()


@router.post("/remove-background/url")
async def remove_background_from_url(
    request: dict,
    current_user_id: str = Depends(get_current_user_id)
):
    """Remove background from an image URL"""
    try:
        image_url = request.get('image_url')
        if not image_url:
            raise HTTPException(status_code=400, detail="image_url is required")
        
        if not background_removal_service.is_configured():
            raise ServiceUnavailableException(
                "Background removal service not available. Please install rembg: pip install rembg"
            )
        
        success, base64_image, error = background_removal_service.remove_background_from_url(image_url)
        
        if success:
            return {
                "success": True,
                "data": {
                    "image_base64": base64_image,
                    "format": "png"
                },
                "message": "Background removed successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=error)
            
    except (ServiceUnavailableException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error removing background from URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-background/base64")
async def remove_background_from_base64(
    request: dict,
    current_user_id: str = Depends(get_current_user_id)
):
    """Remove background from a base64 encoded image"""
    try:
        base64_image = request.get('image_base64')
        if not base64_image:
            raise HTTPException(status_code=400, detail="image_base64 is required")
        
        if not background_removal_service.is_configured():
            raise ServiceUnavailableException(
                "Background removal service not available. Please install rembg: pip install rembg"
            )
        
        success, result_base64, error = background_removal_service.remove_background_from_base64(base64_image)
        
        if success:
            return {
                "success": True,
                "data": {
                    "image_base64": result_base64,
                    "format": "png"
                },
                "message": "Background removed successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=error)
            
    except (ServiceUnavailableException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error removing background from base64: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/remove-background/status")
async def get_background_removal_status(
    current_user_id: str = Depends(get_current_user_id)
):
    """Check if background removal service is configured and get usage info"""
    try:
        is_configured = background_removal_service.is_configured()
        usage_info = None
        
        if is_configured:
            usage_info = background_removal_service.get_api_usage()
        
        return {
            "success": True,
            "data": {
                "configured": is_configured,
                "usage": usage_info
            },
            "message": f"Background removal service is {'configured' if is_configured else 'not configured'}"
        }
        
    except Exception as e:
        logger.error(f"Error getting background removal status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
