"""
File upload router
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
from app.core.logging import get_logger
from app.core.exceptions import ValidationException, StorageException
from app.services.storage_service import StorageService
from app.models.upload import ImageUploadResponse
from app.middleware.auth import get_current_user_id
from config.settings import get_settings

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/unified", response_model=ImageUploadResponse)
async def upload_image_unified(
    file: UploadFile = File(...),
    bucket_name: str = Form(...),
    filename: Optional[str] = Form(None),
    current_user_id: str = Depends(get_current_user_id)
):
    """Unified image upload endpoint for all image types"""
    try:
        logger.info(f"Unified upload request - User: {current_user_id}, Bucket: {bucket_name}")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Reset file pointer
        await file.seek(0)
        
        # Validate file
        if not file.filename:
            raise ValidationException("No filename provided")
        
        if not file.content_type or not file.content_type.startswith('image/'):
            raise ValidationException(f"Invalid file type: {file.content_type}")
        
        # Validate bucket name
        valid_buckets = [settings.storage_bucket, settings.digital_twin_bucket, settings.profile_pictures_bucket]
        if bucket_name not in valid_buckets:
            raise ValidationException(f"Invalid bucket name. Must be one of: {valid_buckets}")
        
        # Validate file content
        if not file_content:
            raise ValidationException("Empty file received")
        
        # Upload using unified method
        image_path = await StorageService.upload_image_unified(
            content=file_content,
            bucket_name=bucket_name,
            filename=filename,
            user_id=current_user_id,
            content_type=file.content_type
        )
        
        if not image_path:
            raise StorageException("Failed to upload image")
        
        return ImageUploadResponse(
            success=True,
            image_path=image_path,
            message="Image uploaded successfully"
        )
        
    except (ValidationException, StorageException):
        raise
    except Exception as e:
        logger.error(f"Error in unified upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{path:path}")
async def serve_image(path: str):
    """Serve images from Supabase storage"""
    try:
        logger.info(f"Image request for path: {path}")
        image_content, content_type = await StorageService.download_image_content(path)
        
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
