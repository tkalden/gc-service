"""
Image serving router
"""

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.services.storage_service import StorageService

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{path:path}")
async def serve_image(path: str):
    """Serve images from Supabase storage"""
    try:
        logger.info(f"Image request for path: {path}")
        logger.info(f"Calling StorageService.download_image_content with path: {path}")
        
        image_content, content_type = await StorageService.download_image_content(path)
        
        logger.info(f"Download result - content length: {len(image_content) if image_content else 0}, content_type: {content_type}")
        
        if not image_content:
            logger.error(f"Failed to download image content for path: {path}")
            raise HTTPException(status_code=404, detail="Image not found")
        
        from fastapi.responses import Response
        return Response(
            content=image_content,
            media_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=3600',
                'Content-Length': str(len(image_content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {path}: {str(e)}")
        raise HTTPException(status_code=404, detail="Image not found")
