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
