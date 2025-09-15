"""
Clothing items router
"""

from fastapi import APIRouter, Depends, HTTPException
from app.core.logging import get_logger
from app.core.exceptions import DatabaseException
from app.services.database_service import DatabaseService
from app.models.clothing import (
    ClothingItemCreate, ClothingItemUpdate, ClothingItemResponse,
    ClothingItemsResponse, DeleteResponse
)
from app.middleware.auth import get_current_user_id

logger = get_logger(__name__)
router = APIRouter()


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
        raise DatabaseException(f"Failed to update clothing item: {str(e)}")


@router.delete("/{item_id}", response_model=DeleteResponse)
async def delete_clothing_item(item_id: str):
    """Delete a clothing item"""
    try:
        # Get the item first to find the image path
        item = await DatabaseService.get_clothing_item_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        
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
