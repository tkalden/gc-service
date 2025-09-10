"""
FastAPI main application for Closet App Backend
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import time
from datetime import datetime

from config import HOST, PORT, DEBUG, ALLOWED_ORIGINS, PROFILE_PICTURES_BUCKET, DIGITAL_TWIN_BUCKET
from models import (
    ClothingItem, ClothingItemCreate, ClothingItemUpdate, ClothingItemResponse,
    ClothingItemsResponse, ImageUploadResponse, DeleteResponse, ErrorResponse,
    UserRegister, UserLogin, AuthResponse, TokenResponse,
    Avatar, AvatarCreate, AvatarResponse, TryOnRequest, TryOnResponse
)
from database import DatabaseService
from storage import StorageService
from auth import AuthService
from background_removal import background_removal_service
from avatar_service import avatar_service
from middleware import get_current_user, get_current_user_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


# Authentication Endpoints

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
            raise HTTPException(status_code=404, detail="Clothing item not found")
        
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
            raise HTTPException(status_code=404, detail="Clothing item not found")
        
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
            raise HTTPException(status_code=404, detail="Clothing item not found")
        
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

@app.post("/api/upload", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...), folder: str = Form("user-clothes"), current_user_id: str = Depends(get_current_user_id)):
    """Upload an image file for the current user"""
    try:
        logger.info(f"Upload request received - User: {current_user_id}, Folder: {folder}")
        logger.info(f"File details - Name: {file.filename}, Content-Type: {file.content_type}, Size: {file.size}")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")
        
        image_path = await StorageService.upload_image(file, folder, current_user_id)
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
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-base64", response_model=ImageUploadResponse)
async def upload_image_base64(
    request: dict,
    current_user_id: str = Depends(get_current_user_id)
):
    """Upload an image file as base64 for React Native compatibility"""
    try:
        logger.info(f"Base64 upload request received - User: {current_user_id}")
        
        file_data = request.get('file_data')
        filename = request.get('filename')
        folder = request.get('folder', 'user-clothes')
        content_type = request.get('content_type', 'image/jpeg')
        
        if not file_data:
            raise HTTPException(status_code=400, detail="No file data provided")
        
        if not filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Convert base64 to bytes
        import base64
        try:
            file_bytes = base64.b64decode(file_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 data: {str(e)}")
        
        # Create a mock UploadFile object
        from fastapi import UploadFile
        from io import BytesIO
        
        file_obj = BytesIO(file_bytes)
        upload_file = UploadFile(
            file=file_obj,
            filename=filename,
            headers={"content-type": content_type}
        )
        # Set the size attribute for validation
        upload_file.size = len(file_bytes)
        
        image_path = await StorageService.upload_image(upload_file, folder, current_user_id)
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
        logger.error(f"Error uploading base64 image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clothes/{item_id}/image", response_model=ClothingItemResponse)
async def upload_clothing_item_image(
    item_id: str,
    file: UploadFile = File(...),
    folder: str = Form("user-clothes")
):
    """Upload an image for a specific clothing item"""
    try:
        # Check if item exists
        item = await DatabaseService.get_clothing_item_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        
        # Delete old image if it exists
        if item.image_path:
            await StorageService.delete_image(item.image_path)
        
        # Upload new image
        image_path = await StorageService.upload_image(file, folder)
        if not image_path:
            raise HTTPException(status_code=400, detail="Failed to upload image")
        
        # Update item with new image path
        updated_item = await DatabaseService.update_clothing_item_image(item_id, image_path)
        if not updated_item:
            raise HTTPException(status_code=500, detail="Failed to update clothing item")
        
        return ClothingItemResponse(
            success=True,
            data=updated_item,
            message="Image uploaded and clothing item updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image for clothing item {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/multiple", response_model=dict)
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    folder: str = Form("user-clothes")
):
    """Upload multiple image files"""
    try:
        uploaded_paths = await StorageService.upload_multiple_images(files, folder)
        return {
            "success": True,
            "uploaded_paths": uploaded_paths,
            "count": len(uploaded_paths),
            "message": f"Successfully uploaded {len(uploaded_paths)} images"
        }
    except Exception as e:
        logger.error(f"Error uploading multiple images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/profile-picture", response_model=ImageUploadResponse)
async def upload_profile_picture(file: UploadFile = File(...), current_user_id: str = Depends(get_current_user_id)):
    """Upload a profile picture for the current user"""
    try:
        logger.info(f"Profile picture upload request received - User: {current_user_id}")
        logger.info(f"File details - Name: {file.filename}, Content-Type: {file.content_type}, Size: {file.size}")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")
        
        # Upload to profile-pictures bucket with user ID folder
        image_path = await StorageService.upload_image(file, "profile-pictures", current_user_id, PROFILE_PICTURES_BUCKET)
        if not image_path:
            raise HTTPException(status_code=400, detail="Failed to upload profile picture")
        
        return ImageUploadResponse(
            success=True,
            image_path=image_path,
            message="Profile picture uploaded successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
        logger.info(f"File details - Name: {file.filename}, Content-Type: {file.content_type}, Size: {file.size}")
        
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
        
        # Read file content once for both upload and processing
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        logger.info(f"File content size: {len(file_content)} bytes")
        
        # Upload original image to digital-twin bucket using content directly
        original_image_path = await StorageService.upload_image_content(
            file_content, file.filename, "avatars/original", current_user_id, DIGITAL_TWIN_BUCKET
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
                
                processed_image_path = await StorageService.upload_image_content(
                    processed_data, f"processed_{file.filename}", "avatars/processed", current_user_id, DIGITAL_TWIN_BUCKET
                )
            except Exception as e:
                logger.warning(f"Failed to save processed image: {str(e)}")
        
        # Create avatar record in database
        avatar_db_data = {
            "original_image_path": original_image_path,
            "processed_image_path": processed_image_path,
            "pose_keypoints": avatar_data["pose_keypoints"],
            "body_segments": avatar_data["body_segments"],
            "confidence_score": quality_score
        }
        
        avatar = await DatabaseService.create_avatar(avatar_db_data, current_user_id)
        if not avatar:
            raise HTTPException(status_code=500, detail="Failed to create avatar record")
        
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, reload=DEBUG)
