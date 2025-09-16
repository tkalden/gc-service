"""
File upload router
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.exceptions import StorageException, ValidationException
from app.core.logging import get_logger
from app.middleware.middleware import get_current_user_id
from app.models.models import ImageUploadResponse
from app.services.storage_service import StorageService
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


@router.get("/debug/supabase")
async def debug_supabase():
    """Debug Supabase client configuration"""
    try:
        from app.services.storage_service import supabase
        settings = get_settings()
        
        return {
            "supabase_url": settings.supabase_url[:50] + "..." if len(settings.supabase_url) > 50 else settings.supabase_url,
            "service_key_length": len(settings.supabase_service_key),
            "supabase_client_initialized": supabase is not None,
            "buckets": supabase.storage.list_buckets() if supabase else "No client"
        }
    except Exception as e:
        return {"error": str(e)}

