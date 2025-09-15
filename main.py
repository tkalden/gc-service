"""
FastAPI main application for Closet App Backend
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from typing import List, Optional
import logging
import time
from datetime import datetime

from config import HOST, PORT, DEBUG, ALLOWED_ORIGINS, PROFILE_PICTURES_BUCKET, DIGITAL_TWIN_BUCKET, STORAGE_BUCKET, BACKEND_URL, MAX_FILE_SIZE
from models import (
    ClothingItem, ClothingItemCreate, ClothingItemUpdate, ClothingItemResponse,
    ClothingItemsResponse, ImageUploadResponse, Base64UploadRequest, DeleteResponse, ErrorResponse,
    UserRegister, UserLogin, AuthResponse, TokenResponse,
    Avatar, AvatarCreate, AvatarResponse, TryOnRequest, TryOnResponse,
    Outfit, OutfitCreate, OutfitUpdate, OutfitResponse, OutfitsResponse, OutfitFilterRequest
)
from database import DatabaseService
from storage import StorageService
from auth import AuthService
from background_removal import background_removal_service
from avatar_service import avatar_service
from outfit_service import outfit_service
from middleware import get_current_user, get_current_user_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CLOTHING_ITEM_NOT_FOUND = "Clothing item not found"
# Constants removed - validation now handled in unified endpoint

# Create FastAPI app
app = FastAPI(
    title="Closet App API",
    description="Backend API for the Closet App",
    version="1.0.0",
    debug=DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Closet App API is running!", "timestamp": datetime.now()}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection (without user filter for health check)
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/api/auth/register", response_model=AuthResponse)
async def register_user(user_data: UserRegister):
    """Register a new user"""
    try:
        result = await AuthService.register_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name
        )
        
        if result["success"]:
            return AuthResponse(
                success=True,
                user=result["user"],
                access_token=result["access_token"],
                message=result["message"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login", response_model=AuthResponse)
async def login_user(user_data: UserLogin):
    """Login user"""
    try:
        result = await AuthService.login_user(
            email=user_data.email,
            password=user_data.password
        )
        
        if result["success"]:
            return AuthResponse(
                success=True,
                user=result["user"],
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token"),
                message=result["message"]
            )
        else:
            raise HTTPException(status_code=401, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/logout")
async def logout_user(current_user: dict = Depends(get_current_user)):
    """Logout current user"""
    try:
        result = await AuthService.logout_user(current_user["id"])
        
        if result["success"]:
            return {"success": True, "message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in logout endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me", response_model=TokenResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return TokenResponse(
        success=True,
        user=current_user,
        message="User information retrieved successfully"
    )


@app.post("/api/auth/reset-password")
async def reset_password(email: str):
    """Send password reset email"""
    try:
        result = await AuthService.reset_password(email)
        
        if result["success"]:
            return {"success": True, "message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset password endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str = Form(...)):
    """Refresh access token"""
    try:
        result = await AuthService.refresh_token(refresh_token)
        
        if result["success"]:
            return AuthResponse(
                success=True,
                user=result["user"],
                access_token=result["access_token"],
                message=result["message"]
            )
        else:
            raise HTTPException(status_code=401, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error in refresh token endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Clothing Items Endpoints

@app.get("/api/clothes", response_model=ClothingItemsResponse)
async def get_all_clothes(current_user_id: str = Depends(get_current_user_id)):
    """Get all clothing items for the current user"""
    try:
        items = await DatabaseService.get_all_clothing_items(current_user_id)
        return ClothingItemsResponse(
            success=True,
            data=items,
            count=len(items),
            message=f"Retrieved {len(items)} clothing items"
        )
    except Exception as e:
        logger.error(f"Error getting all clothes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/clothes/{item_id}", response_model=ClothingItemResponse)
async def get_clothing_item(item_id: str):
    """Get a specific clothing item by ID"""
    try:
        item = await DatabaseService.get_clothing_item_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=CLOTHING_ITEM_NOT_FOUND)
        
        return ClothingItemResponse(
            success=True,
            data=item,
            message="Clothing item retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting clothing item {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clothes", response_model=ClothingItemResponse)
async def create_clothing_item(item_data: ClothingItemCreate, current_user_id: str = Depends(get_current_user_id)):
    """Create a new clothing item for the current user"""
    try:
        logger.info(f"Received clothing item data: {item_data.dict()}")
        logger.info(f"Image path in request: {item_data.image_path}")
        item = await DatabaseService.create_clothing_item(item_data, current_user_id)
        return ClothingItemResponse(
            success=True,
            data=item,
            message="Clothing item created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating clothing item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/clothes/{item_id}", response_model=ClothingItemResponse)
async def update_clothing_item(item_id: str, update_data: ClothingItemUpdate):
    """Update an existing clothing item"""
    try:
        item = await DatabaseService.update_clothing_item(item_id, update_data)
        if not item:
            raise HTTPException(status_code=404, detail=CLOTHING_ITEM_NOT_FOUND)
        
        return ClothingItemResponse(
            success=True,
            data=item,
            message="Clothing item updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating clothing item {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/clothes/{item_id}", response_model=DeleteResponse)
async def delete_clothing_item(item_id: str):
    """Delete a clothing item"""
    try:
        # Get the item first to find the image path
        item = await DatabaseService.get_clothing_item_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=CLOTHING_ITEM_NOT_FOUND)
        
        # Delete the image if it exists
        if item.image_path:
            await StorageService.delete_image(item.image_path)
        
        # Delete the database record
        success = await DatabaseService.delete_clothing_item(item_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete clothing item")
        
        return DeleteResponse(
            success=True,
            message="Clothing item deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting clothing item {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Image Upload Endpoints

# Helper functions removed - validation and bucket determination now handled in unified endpoint

@app.post("/api/upload/unified", response_model=ImageUploadResponse)
async def upload_image_unified(
    file: UploadFile = File(...),
    bucket_name: str = Form(...),
    filename: Optional[str] = Form(None),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Unified image upload endpoint for all image types
    
    Args:
        file: Image file to upload
        bucket_name: Supabase bucket name (clothing-image, digital-twin, profile-picture)
        filename: Optional filename (if not provided, generates uuid.jpg)
        current_user_id: Current user ID for folder structure
    
    Returns:
        ImageUploadResponse with success status and image path
    """
    try:
        logger.info(f"Unified upload request - User: {current_user_id}, Bucket: {bucket_name}, Filename: {filename}")
        # Read file content to get size
        file_content = await file.read()
        file_size = len(file_content)
        logger.info(f"File details - Name: {file.filename}, Content-Type: {file.content_type}, Size: {file_size}")
        
        # Reset file pointer for later use
        await file.seek(0)
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")
        
        # Validate bucket name
        valid_buckets = [STORAGE_BUCKET, DIGITAL_TWIN_BUCKET, PROFILE_PICTURES_BUCKET]
        if bucket_name not in valid_buckets:
            raise HTTPException(status_code=400, detail=f"Invalid bucket name. Must be one of: {valid_buckets}")
        
        # Validate file content
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        # Upload using unified method
        image_path = await StorageService.upload_image_unified(
            content=file_content,
            bucket_name=bucket_name,
            filename=filename,
            user_id=current_user_id,
            content_type=file.content_type
        )
        
        if not image_path:
            raise HTTPException(status_code=400, detail="Failed to upload image")
        
        return ImageUploadResponse(
            success=True,
            image_path=image_path,
            message="Image uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Old upload endpoint removed - use /api/upload/unified instead


# Old base64 upload endpoint removed - use /api/upload/unified instead


# Old multiple upload endpoint removed - use /api/upload/unified instead


@app.get("/api/images/{path:path}")
async def serve_image(path: str):
    """Serve images from Supabase storage"""
    try:
        logger.info(f"Image request for path: {path}")
        image_content, content_type = await StorageService.download_image_content(path)
        
        if not image_content:
            logger.error(f"Failed to download image content for path: {path}")
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Return the image content directly
        from fastapi.responses import Response
        return Response(
            content=image_content,
            media_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=3600',
                'Content-Length': str(len(image_content))
            }
        )
        
    except Exception as e:
        logger.error(f"Error serving image {path}: {str(e)}")
        raise HTTPException(status_code=404, detail="Image not found")




# Utility Endpoints

@app.get("/api/clothes/category/{category}")
async def get_clothes_by_category(category: str):
    """Get clothing items by category"""
    try:
        all_items = await DatabaseService.get_all_clothing_items()
        category_items = [item for item in all_items if item.category.lower() == category.lower()]
        
        return ClothingItemsResponse(
            success=True,
            data=category_items,
            count=len(category_items),
            message=f"Retrieved {len(category_items)} items in category '{category}'"
        )
    except Exception as e:
        logger.error(f"Error getting clothes by category {category}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/clothes/season/{season}")
async def get_clothes_by_season(season: str):
    """Get clothing items by season"""
    try:
        all_items = await DatabaseService.get_all_clothing_items()
        season_items = [
            item for item in all_items 
            if any(s.lower() == season.lower() for s in item.seasons)
        ]
        
        return ClothingItemsResponse(
            success=True,
            data=season_items,
            count=len(season_items),
            message=f"Retrieved {len(season_items)} items for season '{season}'"
        )
    except Exception as e:
        logger.error(f"Error getting clothes by season {season}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Background Removal Endpoints

@app.post("/api/remove-background/url")
async def remove_background_from_url(
    request: dict,
    current_user_id: str = Depends(get_current_user_id)
):
    """Remove background from an image URL"""
    try:
        image_url = request.get('image_url')
        if not image_url:
            raise HTTPException(status_code=400, detail="image_url is required")
        
        logger.info(f"User {current_user_id} requesting background removal for URL: {image_url}")
        
        # Check if service is configured
        if not background_removal_service.is_configured():
            raise HTTPException(
                status_code=503, 
                detail="Background removal service not available. Please install rembg: pip install rembg"
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
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing background from URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/remove-background/base64")
async def remove_background_from_base64(
    request: dict,
    current_user_id: str = Depends(get_current_user_id)
):
    """Remove background from a base64 encoded image"""
    try:
        base64_image = request.get('image_base64')
        if not base64_image:
            raise HTTPException(status_code=400, detail="image_base64 is required")
        
        logger.info(f"User {current_user_id} requesting background removal for base64 image")
        
        # Check if service is configured
        if not background_removal_service.is_configured():
            raise HTTPException(
                status_code=503, 
                detail="Background removal service not available. Please install rembg: pip install rembg"
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
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing background from base64: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/remove-background/status")
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


# Digital Twin Avatar Endpoints

@app.post("/api/avatar/upload", response_model=AvatarResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """Upload and process user avatar for digital twin creation"""
    try:
        logger.info(f"Avatar upload request received - User: {current_user_id}")
        # Read file content to get size
        file_content = await file.read()
        file_size = len(file_content)
        logger.info(f"File details - Name: {file.filename}, Content-Type: {file.content_type}, Size: {file_size}")
        
        # Reset file pointer for later use
        await file.seek(0)
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")
        
        # Check if avatar service is available
        if not avatar_service.is_available():
            raise HTTPException(
                status_code=503, 
                detail="Avatar service not available. Please install MediaPipe: pip install mediapipe"
            )
        
        # Check for existing avatar to clean up old files
        existing_avatar = None
        try:
            existing_avatar = await DatabaseService.get_user_avatar(current_user_id)
            if existing_avatar:
                logger.info(f"Found existing avatar for user: {current_user_id}")
                logger.info(f"Existing avatar paths - Original: {existing_avatar.original_image_path}, Processed: {existing_avatar.processed_image_path}")
            else:
                logger.info(f"No existing avatar found in database for user: {current_user_id}")
        except Exception as e:
            logger.warning(f"Failed to check existing avatar: {str(e)}")
        
        # Validate file content
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        logger.info(f"File content size: {len(file_content)} bytes")
        
        # Upload original image to digital-twin bucket using unified method
        # Use timestamp to ensure unique filename
        timestamp = int(time.time() * 1000)
        original_image_path = await StorageService.upload_image_unified(
            content=file_content,
            bucket_name=DIGITAL_TWIN_BUCKET,
            filename=f"original_{timestamp}",
            user_id=current_user_id,
            content_type=file.content_type
        )
        if not original_image_path:
            raise HTTPException(status_code=400, detail="Failed to upload avatar image")
        
        # Process avatar with AI using the same file content
        success, avatar_data, error = await avatar_service.process_avatar_image(file_content, current_user_id)
        
        if not success:
            # Clean up uploaded file if processing failed
            await StorageService.delete_image(original_image_path)
            raise HTTPException(status_code=400, detail=error)
        
        # Validate avatar quality
        is_valid, message, quality_score = await avatar_service.validate_avatar_quality(avatar_data)
        if not is_valid:
            # Clean up uploaded file if quality is too low
            await StorageService.delete_image(original_image_path)
            raise HTTPException(status_code=400, detail=message)
        
        # Save processed avatar image if available
        processed_image_path = None
        if avatar_data.get("processed_image_base64"):
            try:
                # Decode base64 image and upload directly
                import base64
                processed_data = base64.b64decode(avatar_data["processed_image_base64"])
                
                processed_image_path = await StorageService.upload_image_unified(
                    content=processed_data,
                    bucket_name=DIGITAL_TWIN_BUCKET,
                    filename=f"processed_{timestamp}",
                    user_id=current_user_id,
                    content_type="image/jpeg"
                )
            except Exception as e:
                logger.warning(f"Failed to save processed image: {str(e)}")
        
        # Create or update avatar record in database
        avatar_db_data = {
            "original_image_path": original_image_path,
            "processed_image_path": processed_image_path,
            "pose_keypoints": avatar_data["pose_keypoints"],
            "body_segments": avatar_data["body_segments"],
            "confidence_score": quality_score
        }
        
        avatar = await DatabaseService.upsert_avatar(avatar_db_data, current_user_id)
        if not avatar:
            # Clean up uploaded files if database operation failed
            await StorageService.delete_image(original_image_path)
            if processed_image_path:
                await StorageService.delete_image(processed_image_path)
            raise HTTPException(status_code=500, detail="Failed to create/update avatar record")
        
        # Clean up old avatar files after successful database operation
        if existing_avatar:
            try:
                logger.info(f"Cleaning up old avatar files for user: {current_user_id}")
                
                # Delete old original image if it's different from the new one
                if (existing_avatar.original_image_path and 
                    existing_avatar.original_image_path != original_image_path):
                    delete_result = await StorageService.delete_image(existing_avatar.original_image_path)
                    logger.info(f"Old original image deletion result: {delete_result}")
                
                # Delete old processed image if it's different from the new one
                if (existing_avatar.processed_image_path and 
                    existing_avatar.processed_image_path != processed_image_path):
                    delete_result = await StorageService.delete_image(existing_avatar.processed_image_path)
                    logger.info(f"Old processed image deletion result: {delete_result}")
                    
            except Exception as e:
                logger.warning(f"Failed to clean up old avatar files: {str(e)}")
                # Don't fail the entire operation if cleanup fails
        
        return AvatarResponse(
            success=True,
            data=avatar,
            message=f"Avatar created successfully with quality score: {quality_score:.2f}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/avatar", response_model=AvatarResponse)
async def get_user_avatar(current_user_id: str = Depends(get_current_user_id)):
    """Get user's current avatar"""
    try:
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


@app.get("/api/avatar/{avatar_id}", response_model=AvatarResponse)
async def get_avatar_by_id(avatar_id: str, current_user_id: str = Depends(get_current_user_id)):
    """Get avatar by ID (must belong to current user)"""
    try:
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


@app.post("/api/avatar/try-on")
async def virtual_try_on(
    request: TryOnRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """Perform virtual try-on preview with user's avatar and clothing item"""
    start_time = time.time()
    
    try:
        # Get user's avatar
        avatar = await DatabaseService.get_avatar_by_id(request.avatar_id)
        if not avatar or avatar.user_id != current_user_id:
            raise HTTPException(status_code=404, detail="Avatar not found or access denied")
        
        # Get clothing item
        clothing_item = await DatabaseService.get_clothing_item_by_id(request.clothing_item_id)
        if not clothing_item:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        
        logger.info(f"Generating try-on preview: avatar {avatar.id} + clothing {clothing_item.id}")
        
        # Generate temporary try-on preview (no storage needed)
        try_on_preview = await avatar_service.generate_try_on_preview(
            avatar_path=avatar.original_image_path,
            clothing_path=clothing_item.image_path,
            clothing_name=clothing_item.name,
            clothing_category=clothing_item.category,
            pose_keypoints=avatar.pose_keypoints
        )
        
        if not try_on_preview:
            raise HTTPException(status_code=500, detail="Failed to generate try-on preview")
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "data": {
                "preview_image": try_on_preview["image_base64"],
                "confidence_score": try_on_preview["confidence"],
                "processing_time": processing_time,
                "clothing_item_name": clothing_item.name,
                "avatar_id": avatar.id,
                "clothing_item_id": clothing_item.id
            },
            "message": f"Try-on preview generated in {processing_time:.2f}s"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing virtual try-on: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/avatar/try-on/history")
async def get_tryon_history(
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get user's virtual try-on history"""
    try:
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


@app.get("/api/avatar/service/status")
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


# Outfit Endpoints

@app.post("/api/outfits", response_model=OutfitResponse)
async def create_outfit(
    outfit_data: OutfitCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new outfit (for outfits with existing image URLs)"""
    try:
        # Convert Pydantic model to dict
        outfit_dict = outfit_data.dict()
        
        # Use service to create outfit
        outfit = await outfit_service.create_outfit_simple(outfit_dict, current_user_id)
        
        return OutfitResponse(
            success=True,
            data=outfit,
            message="Outfit created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# WARNING: This endpoint is for outfit-specific images, NOT clothing item images
# Regular outfit creation should use /api/outfits/generate which references existing clothing items
@app.post("/api/outfits/upload", response_model=OutfitResponse)
async def create_outfit_with_images(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    clothing_item_ids: Optional[str] = Form(None),
    outfit_date: Optional[str] = Form(None),
    season: Optional[str] = Form(None),
    occasion: Optional[str] = Form(None),
    weather_condition: Optional[str] = Form(None),
    rating: Optional[int] = Form(None),
    is_favorite: bool = Form(False),
    tags: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new outfit with image uploads"""
    try:
        # Prepare outfit data from form
        outfit_data = {
            "name": name,
            "description": description,
            "clothing_item_ids": clothing_item_ids,
            "outfit_date": outfit_date,
            "season": season,
            "occasion": occasion,
            "weather_condition": weather_condition,
            "rating": rating,
            "is_favorite": is_favorite,
            "tags": tags
        }
        
        # Use service to create outfit with images
        outfit = await outfit_service.create_outfit_with_images(
            outfit_data=outfit_data,
            image_files=files,
            user_id=current_user_id
        )
        
        return OutfitResponse(
            success=True,
            data=outfit,
            message=f"Outfit created successfully with {len(files)} images"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating outfit with images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/outfits/generate", response_model=OutfitResponse)
async def generate_outfit_from_items(
    outfit_data: OutfitCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create outfit from clothing items (no image generation needed)"""
    try:
        logger.info(f"Creating outfit from clothing items for user: {current_user_id}")
        
        outfit_dict = outfit_data.dict()
        clothing_item_ids = outfit_dict.get("clothing_item_ids", [])
        
        if not clothing_item_ids:
            raise HTTPException(status_code=400, detail="No clothing items provided")
        
        # Verify clothing items exist and belong to user (security check + race condition protection)
        clothing_items = await DatabaseService.get_clothing_items_by_ids(clothing_item_ids, current_user_id)
        
        if not clothing_items:
            raise HTTPException(status_code=400, detail="No valid clothing items found")
        
        # Log warning if some items are missing (but don't fail the request)
        if len(clothing_items) != len(clothing_item_ids):
            missing_count = len(clothing_item_ids) - len(clothing_items)
            logger.warning(f"User {current_user_id} tried to create outfit with {missing_count} missing/invalid clothing items")
            # Continue with the valid items instead of failing
        
        outfit = await outfit_service.create_outfit_simple(outfit_dict, current_user_id)
        
        if not outfit:
            raise HTTPException(status_code=500, detail="Failed to create outfit")
        
        return OutfitResponse(
            success=True,
            data=outfit,
            message=f"Outfit created successfully with {len(clothing_items)} clothing items"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outfits", response_model=OutfitsResponse)
async def get_user_outfits(
    current_user_id: str = Depends(get_current_user_id),
    season: Optional[str] = None,
    occasion: Optional[str] = None,
    weather_condition: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_rating: Optional[int] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    limit: int = 20,
    offset: int = 0
):
    """Get user's outfits with optional filtering"""
    try:
        logger.info(f"Getting outfits for user: {current_user_id}")
        logger.info(f"Request parameters - start_date: {start_date}, end_date: {end_date}, season: {season}, occasion: {occasion}")
        
        # Prepare filters
        filters = {}
        if season:
            filters["season"] = season
        if occasion:
            filters["occasion"] = occasion
        if weather_condition:
            filters["weather_condition"] = weather_condition
        if is_favorite is not None:
            filters["is_favorite"] = is_favorite
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if min_rating:
            filters["min_rating"] = min_rating
        if tags:
            # Parse comma-separated tags
            filters["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        logger.info(f"Prepared filters: {filters}")
        
        # Get outfits from database
        outfits = await DatabaseService.get_user_outfits(
            current_user_id, 
            limit=limit, 
            offset=offset, 
            filters=filters if filters else None
        )
        
        # Get total count for pagination
        total_count = await DatabaseService.get_outfit_count(
            current_user_id, 
            filters=filters if filters else None
        )
        
        return OutfitsResponse(
            success=True,
            data=outfits,
            count=total_count,
            message=f"Retrieved {len(outfits)} outfits"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user outfits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outfits/{outfit_id}", response_model=OutfitResponse)
async def get_outfit_by_id(
    outfit_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get outfit by ID"""
    try:
        logger.info(f"Getting outfit {outfit_id} for user: {current_user_id}")
        
        outfit = await DatabaseService.get_outfit_by_id(outfit_id, current_user_id)
        
        if not outfit:
            raise HTTPException(status_code=404, detail="Outfit not found")
        
        return OutfitResponse(
            success=True,
            data=outfit,
            message="Outfit retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting outfit by ID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outfits/{outfit_id}/details")
async def get_outfit_details_with_clothing_items(
    outfit_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get outfit details with clothing item information for rendering"""
    try:
        logger.info(f"Getting outfit details {outfit_id} for user: {current_user_id}")
        
        # Get outfit
        outfit = await DatabaseService.get_outfit_by_id(outfit_id, current_user_id)
        
        if not outfit:
            raise HTTPException(status_code=404, detail="Outfit not found")
        
        # Get clothing items for this outfit
        clothing_items = []
        if outfit.clothing_item_ids:
            clothing_items = await DatabaseService.get_clothing_items_by_ids(
                outfit.clothing_item_ids, 
                current_user_id
            )
        
        # Convert clothing items to dict format for frontend
        clothing_items_data = []
        for item in clothing_items:
            clothing_items_data.append({
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "image_path": item.image_path,
                "seasons": item.seasons,
                "metadata": item.metadata
            })
        
        return {
            "success": True,
            "data": {
                "outfit": {
                    "id": outfit.id,
                    "name": outfit.name,
                    "description": outfit.description,
                    "outfit_date": outfit.outfit_date,
                    "season": outfit.season,
                    "occasion": outfit.occasion,
                    "weather_condition": outfit.weather_condition,
                    "rating": outfit.rating,
                    "is_favorite": outfit.is_favorite,
                    "tags": outfit.tags,
                    "is_collage": outfit.is_collage,
                    "canvas_layout": outfit.canvas_layout,
                    "created_at": outfit.created_at,
                    "updated_at": outfit.updated_at
                },
                "clothing_items": clothing_items_data
            },
            "message": "Outfit details retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting outfit details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/outfits/{outfit_id}", response_model=OutfitResponse)
async def update_outfit(
    outfit_id: str,
    outfit_data: OutfitUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update outfit"""
    try:
        logger.info(f"Updating outfit {outfit_id} for user: {current_user_id}")
        
        # Convert Pydantic model to dict, excluding None values
        outfit_dict = outfit_data.dict(exclude_unset=True)
        
        # Update outfit in database
        outfit = await DatabaseService.update_outfit(outfit_id, outfit_dict, current_user_id)
        
        if not outfit:
            raise HTTPException(status_code=404, detail="Outfit not found or access denied")
        
        return OutfitResponse(
            success=True,
            data=outfit,
            message="Outfit updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/outfits/{outfit_id}", response_model=DeleteResponse)
async def delete_outfit(
    outfit_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete outfit and associated images"""
    try:
        # Use service to delete outfit with cleanup
        await outfit_service.delete_outfit_with_cleanup(outfit_id, current_user_id)
        
        return DeleteResponse(
            success=True,
            message="Outfit and associated images deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting outfit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/outfits/filter", response_model=OutfitsResponse)
async def filter_outfits(
    filter_request: OutfitFilterRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """Filter outfits with advanced criteria"""
    try:
        logger.info(f"Filtering outfits for user: {current_user_id}")
        
        # Convert Pydantic model to dict, excluding None values
        filters = filter_request.dict(exclude_unset=True)
        
        # Remove pagination parameters from filters
        limit = filters.pop("limit", 20)
        offset = filters.pop("offset", 0)
        
        # Get filtered outfits from database
        outfits = await DatabaseService.get_user_outfits(
            current_user_id, 
            limit=limit, 
            offset=offset, 
            filters=filters if filters else None
        )
        
        # Get total count for pagination
        total_count = await DatabaseService.get_outfit_count(
            current_user_id, 
            filters=filters if filters else None
        )
        
        return OutfitsResponse(
            success=True,
            data=outfits,
            count=total_count,
            message=f"Retrieved {len(outfits)} filtered outfits"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filtering outfits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)

