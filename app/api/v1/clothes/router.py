"""
Clothing items router
"""

from fastapi import APIRouter, Depends, HTTPException
from app.core.logging import get_logger
from app.core.exceptions import DatabaseException
from app.services.database_service import DatabaseService
from app.models.models import (
    ClothingItemCreate, ClothingItemUpdate, ClothingItemResponse,
    ClothingItemsResponse, DeleteResponse
)
from app.middleware.middleware import get_current_user_id

logger = get_logger(__name__)
router = APIRouter()

# Constants
CLOTHING_ITEM_NOT_FOUND = "Clothing item not found"


@router.get("", response_model=ClothingItemsResponse)
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
        raise DatabaseException(f"Failed to retrieve clothing items: {str(e)}")


@router.get("/{item_id}", response_model=ClothingItemResponse)
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
        raise DatabaseException(f"Failed to retrieve clothing item: {str(e)}")


@router.post("", response_model=ClothingItemResponse)
async def create_clothing_item(
    item_data: ClothingItemCreate, 
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new clothing item for the current user"""
    try:
        logger.info(f"Creating clothing item for user: {current_user_id}")
        item = await DatabaseService.create_clothing_item(item_data, current_user_id)
        return ClothingItemResponse(
            success=True,
            data=item,
            message="Clothing item created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating clothing item: {str(e)}")
        raise DatabaseException(f"Failed to create clothing item: {str(e)}")


@router.put("/{item_id}", response_model=ClothingItemResponse)
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
        raise DatabaseException(f"Failed to update clothing item: {str(e)}")


@router.delete("/{item_id}", response_model=DeleteResponse)
async def delete_clothing_item(item_id: str):
    """Delete a clothing item"""
    try:
        # Get the item first to find the image path
        item = await DatabaseService.get_clothing_item_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=CLOTHING_ITEM_NOT_FOUND)
        
        # Delete the image if it exists
        if item.image_path:
            from app.services.storage_service import StorageService
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
        raise DatabaseException(f"Failed to delete clothing item: {str(e)}")


@router.get("/category/{category}", response_model=ClothingItemsResponse)
async def get_clothes_by_category(
    category: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get clothing items by category"""
    try:
        all_items = await DatabaseService.get_all_clothing_items(current_user_id)
        category_items = [item for item in all_items if item.category.lower() == category.lower()]
        
        return ClothingItemsResponse(
            success=True,
            data=category_items,
            count=len(category_items),
            message=f"Retrieved {len(category_items)} items in category '{category}'"
        )
    except Exception as e:
        logger.error(f"Error getting clothes by category {category}: {str(e)}")
        raise DatabaseException(f"Failed to retrieve clothing items by category: {str(e)}")


@router.get("/season/{season}", response_model=ClothingItemsResponse)
async def get_clothes_by_season(
    season: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get clothing items by season"""
    try:
        all_items = await DatabaseService.get_all_clothing_items(current_user_id)
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
        raise DatabaseException(f"Failed to retrieve clothing items by season: {str(e)}")
