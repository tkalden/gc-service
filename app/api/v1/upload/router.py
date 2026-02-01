"""
File upload router
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.exceptions import StorageException, ValidationException
from app.core.logging import get_logger
from app.middleware.middleware import get_current_user_id
from app.models.models import ImageUploadResponse
from app.services.background_removal import BackgroundRemovalService
from app.services.clothing_classifier import clothing_classifier
from app.services.enhanced_clothing_classifier import \
    EnhancedClothingClassifier
from app.services.storage_service import StorageService
from app.services.title_generator import TitleGenerator
from config.settings import get_settings

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()

# Initialize services
background_removal_service = BackgroundRemovalService()
logger.info(f"Background removal service initialized - configured: {background_removal_service.is_configured()}")
logger.info(f"Better session available: {background_removal_service.better_session is not None}")
logger.info(f"Fallback session available: {background_removal_service.session is not None}")

enhanced_classifier = EnhancedClothingClassifier(
    model_path="/Users/tenzinkalden/gc-service/models/clothes_classifier_model.h5"
)
title_generator = TitleGenerator()


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


@router.post("/remove-background/base64")
async def remove_background_from_base64(
    request: dict,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Remove background from a base64 encoded image (User-level endpoint)
    
    Request body:
    {
        "image_base64": "base64_string",
        "auto_crop": false  // Optional, default: false
    }
    """
    try:
        base64_image = request.get('image_base64')
        if not base64_image:
            raise HTTPException(status_code=400, detail="image_base64 is required")
        
        auto_crop = request.get('auto_crop', False)
        
        if not background_removal_service.is_configured():
            raise HTTPException(
                status_code=503,
                detail="Background removal service not available. Please install rembg: pip install rembg"
            )
        
        success, result_base64, error = background_removal_service.remove_background_from_base64(
            base64_image, 
            auto_crop=auto_crop
        )
        
        if success:
            return {
                "success": True,
                "data": {
                    "image_base64": result_base64,
                    "format": "png",
                    "background_removed": True
                },
                "message": "Background removed successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=error or "Background removal failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing background: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify-clothing")
async def classify_clothing(
    request: dict,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Classify clothing from base64 image
    
    Request body:
    {
        "image_base64": "base64_encoded_string"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "category": "Tops",
            "ml_label": "t-shirt",
            "confidence": 0.95,
            "all_scores": {...}
        }
    }
    """
    try:
        base64_image = request.get('image_base64')
        if not base64_image:
            raise HTTPException(status_code=400, detail="image_base64 is required")
        
        logger.info(f"Classification request from user: {current_user_id}")
        logger.info("Starting clothing classification")
        logger.info(f"Base64 image length: {len(base64_image)}")
        
        # Classify clothing
        success, category, ml_label, info = clothing_classifier.classify_from_base64(base64_image)
        
        if not success:
            logger.warning("Classification failed, using defaults")
            category, ml_label = "Tops", "unknown"
            info = {"confidence": 0.0, "all_scores": {}}
        
        confidence = info.get('confidence', 0.0)
        all_scores = info.get('all_scores', {})
        
        logger.info(f"Classification complete - Category: {category}, Confidence: {confidence}")
        
        return {
            "success": True,
            "data": {
                "category": category,
                "ml_label": ml_label,
                "confidence": confidence,
                "all_scores": all_scores
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in clothing classification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/smart-upload-async")
async def smart_upload_async(
    request: dict,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Async smart upload: Call background removal and classification in parallel
    
    Request body:
    {
        "image_base64": "base64_encoded_string"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "image_base64": "processed_image",
            "category": "Tops",
            "ml_label": "t-shirt", 
            "confidence": 0.95,
            "background_removed": true,
            "classification_available": true
        }
    }
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    try:
        base64_image = request.get('image_base64')
        if not base64_image:
            raise HTTPException(status_code=400, detail="image_base64 is required")
        
        logger.info(f"Smart upload request from user: {current_user_id}")
        logger.info("Starting async processing: background removal + classification")
        logger.info(f"Base64 image length: {len(base64_image)}")
        
        # Create executor for CPU-bound operations
        executor = ThreadPoolExecutor(max_workers=2)
        loop = asyncio.get_event_loop()
        
        # Create async tasks for both operations using ThreadPoolExecutor
        async def run_background_removal():
            try:
                logger.info("Starting background removal in smart upload...")
                logger.info(f"Service configured: {background_removal_service.is_configured()}")
                logger.info(f"Better session: {background_removal_service.better_session is not None}")
                logger.info(f"Fallback session: {background_removal_service.session is not None}")
                if background_removal_service.is_configured():
                    # Run in thread pool since it's CPU-bound
                    success, result, error = await loop.run_in_executor(
                        executor,
                        lambda: background_removal_service.remove_background_from_base64(
                            base64_image, auto_crop=False
                        )
                    )
                    logger.info(f"Background removal result: success={success}, error={error}")
                    return {
                        "success": success,
                        "image_base64": result if success else base64_image,
                        "error": error
                    }
                else:
                    logger.warning("Background removal not available, using original image")
                    return {
                        "success": False,
                        "image_base64": base64_image,
                        "error": "Background removal service not available"
                    }
            except Exception as e:
                logger.error(f"Background removal error: {str(e)}")
                return {
                    "success": False,
                    "image_base64": base64_image,
                    "error": str(e)
                }
        
        async def run_classification():
            try:
                # Use enhanced classification with season detection in thread pool
                success, category, ml_label, confidence_scores, season_scores = await loop.run_in_executor(
                    executor,
                    lambda: enhanced_classifier.classify_with_season(base64_image)
                )
                
                if not success:
                    # Fallback to basic classification
                    logger.warning("Enhanced classification failed, trying basic classification")
                    success, category, ml_label, info = clothing_classifier.classify_from_base64(base64_image)
                    if success:
                        confidence = info.get('confidence', 0.0)
                        season_scores = {'spring': 0.25, 'summer': 0.25, 'fall': 0.25, 'winter': 0.25}
                    else:
                        confidence = 0.0
                        season_scores = {'spring': 0.25, 'summer': 0.25, 'fall': 0.25, 'winter': 0.25}
                else:
                    confidence = confidence_scores.get('category', 0.0)
                
                # Get best season
                best_season, season_confidence = enhanced_classifier.get_best_season(season_scores)
                
                # Generate title
                title = title_generator.generate_title(
                    category=category,
                    season=best_season,
                    ml_label=ml_label
                )
                
                # Generate multiple title options
                title_options = title_generator.generate_multiple_titles(
                    category=category,
                    season=best_season,
                    ml_label=ml_label,
                    count=3
                )
                
                # Get seasonal recommendations
                seasonal_recommendations = enhanced_classifier.get_seasonal_recommendations(season_scores, category)
                
                return {
                    "success": success,
                    "category": category,
                    "ml_label": ml_label,
                    "confidence": confidence,
                    "season": best_season,
                    "season_confidence": season_confidence,
                    "all_season_scores": season_scores,
                    "title": title,
                    "title_options": title_options,
                    "seasonal_recommendations": seasonal_recommendations,
                    "error": ml_label if not success else None
                }
            except Exception as e:
                logger.error(f"Enhanced classification error: {str(e)}")
                return {
                    "success": False,
                    "category": "Tops",
                    "ml_label": "unknown",
                    "confidence": 0.0,
                    "season": "spring",
                    "season_confidence": 0.25,
                    "all_season_scores": {'spring': 0.25, 'summer': 0.25, 'fall': 0.25, 'winter': 0.25},
                    "title": "Stylish Tops",
                    "title_options": ["Stylish Tops", "Fashionable Tops", "Trendy Tops"],
                    "seasonal_recommendations": [],
                    "error": str(e)
                }
        
        # Run both operations in parallel
        bg_task = asyncio.create_task(run_background_removal())
        clf_task = asyncio.create_task(run_classification())
        
        # Wait for both to complete
        bg_result, clf_result = await asyncio.gather(bg_task, clf_task)
        
        logger.info(f"Background removal: {'success' if bg_result['success'] else 'failed'}")
        logger.info(f"Classification: {'success' if clf_result['success'] else 'failed'}")
        
        return {
            "success": True,
            "data": {
                "image_base64": bg_result["image_base64"],
                "category": clf_result["category"],
                "ml_label": clf_result["ml_label"],
                "confidence": clf_result["confidence"],
                "season": clf_result.get("season", "spring"),
                "season_confidence": clf_result.get("season_confidence", 0.25),
                "all_season_scores": clf_result.get("all_season_scores", {}),
                "title": clf_result.get("title", "Stylish Item"),
                "title_options": clf_result.get("title_options", []),
                "seasonal_recommendations": clf_result.get("seasonal_recommendations", []),
                "format": "png",
                "background_removed": bg_result["success"],
                "classification_available": clf_result["success"],
                "ai_features": {
                    "classification": clf_result["success"],
                    "season_detection": True,
                    "title_generation": True,
                    "background_removal": bg_result["success"]
                },
                "background_error": bg_result.get("error"),
                "classification_error": clf_result.get("error")
            },
            "message": f"AI processing complete. {clf_result['category']} - {clf_result.get('season', 'spring')} season - {clf_result.get('title', 'Item')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in async smart upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

