"""
Outfits router
"""

from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from typing import List, Optional
from app.core.logging import get_logger
from app.core.exceptions import DatabaseException
from app.services.outfit_service import outfit_service
from app.models.models import (
    OutfitCreate, OutfitUpdate, OutfitResponse, 
    OutfitsResponse, OutfitFilterRequest, DeleteResponse
)
from app.middleware.middleware import get_current_user_id

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=OutfitResponse)
async def create_outfit(
    outfit_data: OutfitCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new outfit"""
    try:
        outfit_dict = outfit_data.dict()
        outfit = await outfit_service.create_outfit_simple(outfit_dict, current_user_id)
        
        return OutfitResponse(
            success=True,
            data=outfit,
            message="Outfit created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating outfit: {str(e)}")
        raise DatabaseException(f"Failed to create outfit: {str(e)}")


@router.post("/upload", response_model=OutfitResponse)
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
    except Exception as e:
        logger.error(f"Error creating outfit with images: {str(e)}")
        raise DatabaseException(f"Failed to create outfit: {str(e)}")


@router.get("", response_model=OutfitsResponse)
async def get_user_outfits(
    current_user_id: str = Depends(get_current_user_id),
    season: Optional[str] = None,
    occasion: Optional[str] = None,
    weather_condition: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_rating: Optional[int] = None,
    tags: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """Get user's outfits with optional filtering"""
    try:
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
            filters["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        from app.services.database_service import DatabaseService
        outfits = await DatabaseService.get_user_outfits(
            current_user_id, 
            limit=limit, 
            offset=offset, 
            filters=filters if filters else None
        )
        
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
    except Exception as e:
        logger.error(f"Error getting user outfits: {str(e)}")
        raise DatabaseException(f"Failed to retrieve outfits: {str(e)}")


@router.get("/{outfit_id}", response_model=OutfitResponse)
async def get_outfit_by_id(
    outfit_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get outfit by ID"""
    try:
        from app.services.database_service import DatabaseService
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
        raise DatabaseException(f"Failed to retrieve outfit: {str(e)}")


@router.put("/{outfit_id}", response_model=OutfitResponse)
async def update_outfit(
    outfit_id: str,
    outfit_data: OutfitUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update outfit"""
    try:
        outfit_dict = outfit_data.dict(exclude_unset=True)
        
        from app.services.database_service import DatabaseService
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
        raise DatabaseException(f"Failed to update outfit: {str(e)}")


@router.delete("/{outfit_id}", response_model=DeleteResponse)
async def delete_outfit(
    outfit_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete outfit and associated images"""
    try:
        await outfit_service.delete_outfit_with_cleanup(outfit_id, current_user_id)
        
        return DeleteResponse(
            success=True,
            message="Outfit and associated images deleted successfully"
        )
    except Exception as e:
        logger.error(f"Error deleting outfit: {str(e)}")
        raise DatabaseException(f"Failed to delete outfit: {str(e)}")


@router.post("/generate", response_model=OutfitResponse)
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
        
        # Verify clothing items exist and belong to user
        from app.services.database_service import DatabaseService
        clothing_items = await DatabaseService.get_clothing_items_by_ids(clothing_item_ids, current_user_id)
        
        if not clothing_items:
            raise HTTPException(status_code=400, detail="No valid clothing items found")
        
        # Log warning if some items are missing
        if len(clothing_items) != len(clothing_item_ids):
            missing_count = len(clothing_item_ids) - len(clothing_items)
            logger.warning(f"User {current_user_id} tried to create outfit with {missing_count} missing/invalid clothing items")
        
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
        raise DatabaseException(f"Failed to create outfit: {str(e)}")


@router.get("/{outfit_id}/details")
async def get_outfit_details_with_clothing_items(
    outfit_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get outfit details with clothing item information for rendering"""
    try:
        logger.info(f"Getting outfit details {outfit_id} for user: {current_user_id}")
        
        from app.services.database_service import DatabaseService
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
        raise DatabaseException(f"Failed to retrieve outfit details: {str(e)}")


@router.post("/filter", response_model=OutfitsResponse)
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
        
        from app.services.database_service import DatabaseService
        outfits = await DatabaseService.get_user_outfits(
            current_user_id, 
            limit=limit, 
            offset=offset, 
            filters=filters if filters else None
        )
        
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
    except Exception as e:
        logger.error(f"Error filtering outfits: {str(e)}")
        raise DatabaseException(f"Failed to filter outfits: {str(e)}")
