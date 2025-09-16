"""
Outfit Service for managing user outfits with image uploads
"""

import os
import time
import json
import logging
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageDraw, ImageFont
import io

from app.services.database_service import DatabaseService
from app.services.storage_service import StorageService
from app.models.models import Outfit, OutfitCreate, OutfitUpdate

logger = logging.getLogger(__name__)

# Constants
OUTFIT_NOT_FOUND_ERROR = "Outfit not found or access denied"


class OutfitService:
    """Service for managing outfit operations with transactional image handling"""
    
    def __init__(self):
        self.max_images_per_outfit = 10
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    async def create_outfit_with_images(
        self,
        outfit_data: Dict[str, Any],
        image_files: List[UploadFile],
        user_id: str
    ) -> Outfit:
        """
        Create outfit with image uploads in a transactional manner
        If any step fails, cleanup is performed
        
        WARNING: This is for outfit-specific images, NOT clothing item images.
        Regular outfit creation should use create_outfit_simple() which references existing clothing items.
        """
        try:
            logger.info(f"Creating outfit with {len(image_files)} images for user: {user_id}")
            
            # Validate inputs
            self._validate_outfit_data(outfit_data)
            self._validate_image_files(image_files)
            
            # Upload images first
            uploaded_image_paths = await self._upload_images(image_files, user_id)
            
            try:
                # Prepare outfit data with uploaded image paths
                outfit_dict = self._prepare_outfit_data(outfit_data, uploaded_image_paths)
                
                # Create outfit in database
                outfit = await DatabaseService.create_outfit(outfit_dict, user_id)
                
                if not outfit:
                    # If database save fails, clean up uploaded images
                    await self._cleanup_images(uploaded_image_paths)
                    raise HTTPException(status_code=500, detail="Failed to create outfit record")
                
                logger.info(f"Successfully created outfit {outfit.id} with {len(uploaded_image_paths)} images")
                return outfit
                
            except Exception as e:
                # If database save fails, clean up uploaded images
                logger.error(f"Database save failed: {str(e)}")
                await self._cleanup_images(uploaded_image_paths)
                raise HTTPException(status_code=500, detail=f"Failed to save outfit: {str(e)}")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating outfit with images: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def create_outfit_simple(
        self,
        outfit_data: Dict[str, Any],
        user_id: str
    ) -> Outfit:
        """Create outfit - use image_urls from frontend if provided, otherwise get from clothing items"""
        try:
            logger.info(f"Creating outfit for user: {user_id}")
            
            self._validate_outfit_data(outfit_data)
            
            # Check if frontend provided image_urls directly (more efficient)
            image_urls = outfit_data.get("image_urls", [])
            
            # If no image_urls provided, get them from clothing items (fallback)
            if not image_urls:
                clothing_item_ids = outfit_data.get("clothing_item_ids", [])
                if clothing_item_ids:
                    try:
                        clothing_items = await DatabaseService.get_clothing_items_by_ids(clothing_item_ids, user_id)
                        image_urls = [item.image_path for item in clothing_items if item.image_path]
                        logger.info(f"Fallback: Found {len(image_urls)} clothing item images from database")
                    except Exception as e:
                        logger.warning(f"Failed to get clothing item images: {str(e)}")
                else:
                    logger.info("No clothing items provided, outfit will have no images")
            
            # Prepare outfit data with image URLs
            outfit_dict = self._prepare_outfit_data(outfit_data, image_urls)
            
            outfit = await DatabaseService.create_outfit(outfit_dict, user_id)
            
            if not outfit:
                raise HTTPException(status_code=500, detail="Failed to create outfit")
            
            logger.info(f"Successfully created outfit {outfit.id} with {len(image_urls)} images")
            return outfit
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating outfit: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def update_outfit_with_cleanup(
        self,
        outfit_id: str,
        outfit_data: Dict[str, Any],
        user_id: str,
        new_image_files: Optional[List[UploadFile]] = None
    ) -> Outfit:
        """
        Update outfit with optional new image uploads
        Handles cleanup of old images when new ones are uploaded
        """
        try:
            logger.info(f"Updating outfit {outfit_id} for user: {user_id}")
            
            # Get existing outfit
            existing_outfit = await DatabaseService.get_outfit_by_id(outfit_id, user_id)
            if not existing_outfit:
                raise HTTPException(status_code=404, detail=OUTFIT_NOT_FOUND_ERROR)
            
            old_image_paths = existing_outfit.image_urls.copy() if existing_outfit.image_urls else []
            new_image_paths = []
            
            # Upload new images if provided
            if new_image_files:
                self._validate_image_files(new_image_files)
                new_image_paths = await self._upload_images(new_image_files, user_id)
            
            try:
                # Prepare update data
                update_data = self._prepare_outfit_data(outfit_data, new_image_paths)
                
                # Update outfit in database
                updated_outfit = await DatabaseService.update_outfit(outfit_id, update_data, user_id)
                
                if not updated_outfit:
                    # If update fails, clean up new images
                    await self._cleanup_images(new_image_paths)
                    raise HTTPException(status_code=500, detail="Failed to update outfit")
                
                # Clean up old images that are no longer needed
                if new_image_paths and old_image_paths:
                    await self._cleanup_old_images(old_image_paths, new_image_paths)
                
                return updated_outfit
                
            except Exception as e:
                # If update fails, clean up new images
                await self._cleanup_images(new_image_paths)
                raise HTTPException(status_code=500, detail=f"Failed to update outfit: {str(e)}")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating outfit: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_outfit_with_cleanup(
        self,
        outfit_id: str,
        user_id: str
    ) -> bool:
        """Delete outfit (DO NOT delete clothing item images - they are shared)"""
        try:
            logger.info(f"Deleting outfit {outfit_id} for user: {user_id}")
            
            # Get outfit to verify it exists
            outfit = await DatabaseService.get_outfit_by_id(outfit_id, user_id)
            if not outfit:
                raise HTTPException(status_code=404, detail=OUTFIT_NOT_FOUND_ERROR)
            
            # Delete outfit from database only
            success = await DatabaseService.delete_outfit(outfit_id, user_id)
            
            if not success:
                raise HTTPException(status_code=404, detail=OUTFIT_NOT_FOUND_ERROR)
            
            # DO NOT delete image_urls - they are references to shared clothing item images
            # Clothing items are shared across multiple outfits and should never be deleted
            # when an outfit is deleted
            
            logger.info(f"Successfully deleted outfit {outfit_id} (clothing item images preserved)")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting outfit: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _validate_outfit_data(self, outfit_data: Dict[str, Any]) -> None:
        """Validate outfit data"""
        if not outfit_data.get("name", "").strip():
            raise HTTPException(status_code=400, detail="Outfit name is required")
        
        if len(outfit_data.get("name", "")) > 100:
            raise HTTPException(status_code=400, detail="Outfit name too long (max 100 characters)")
        
        if outfit_data.get("description") and len(outfit_data["description"]) > 500:
            raise HTTPException(status_code=400, detail="Description too long (max 500 characters)")
        
        if outfit_data.get("rating") and (outfit_data["rating"] < 1 or outfit_data["rating"] > 5):
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        if outfit_data.get("tags") and len(outfit_data["tags"]) > 20:
            raise HTTPException(status_code=400, detail="Too many tags (max 20)")
    
    def _validate_image_files(self, image_files: List[UploadFile]) -> None:
        """Validate image files"""
        if not image_files or len(image_files) == 0:
            raise HTTPException(status_code=400, detail="At least one image file is required")
        
        if len(image_files) > self.max_images_per_outfit:
            raise HTTPException(status_code=400, detail=f"Maximum {self.max_images_per_outfit} images allowed per outfit")
        
        for file in image_files:
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")
            
            # Check file size
            if hasattr(file, 'size') and file.size > self.max_file_size:
                raise HTTPException(status_code=400, detail=f"File {file.filename} is too large")
    
    async def _upload_images(self, image_files: List[UploadFile], user_id: str) -> List[str]:
        """Upload multiple images and return their paths"""
        uploaded_paths = []
        timestamp = int(time.time() * 1000)
        
        try:
            for i, file in enumerate(image_files):
                # Read file content
                file_content = await file.read()
                
                # Validate file size after reading
                if len(file_content) > self.max_file_size:
                    raise HTTPException(status_code=400, detail=f"File {file.filename} is too large")
                
                # Generate unique filename
                file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
                filename = f"outfit_{timestamp}_{i}_{user_id}.{file_extension}"
                
                # Upload to storage
                image_path = await StorageService.upload_image_unified(
                    content=file_content,
                    bucket_name="storage",  # Use main storage bucket
                    filename=filename,
                    user_id=user_id,
                    content_type=file.content_type
                )
                
                if not image_path:
                    raise HTTPException(status_code=500, detail=f"Failed to upload image {file.filename}")
                
                uploaded_paths.append(image_path)
                logger.info(f"Uploaded image {i+1}/{len(image_files)}: {image_path}")
            
            return uploaded_paths
            
        except (HTTPException, ValueError, OSError) as e:
            # Clean up any uploaded images if upload fails
            logger.error(f"Image upload failed: {str(e)}")
            await self._cleanup_images(uploaded_paths)
            raise HTTPException(status_code=500, detail=f"Failed to upload images: {str(e)}")
    
    def _prepare_outfit_data(self, outfit_data: Dict[str, Any], image_paths: List[str]) -> Dict[str, Any]:
        """Prepare outfit data for database storage"""
        prepared_data = {
            "name": outfit_data.get("name", "").strip(),
            "description": outfit_data.get("description"),
            "image_urls": image_paths,
            "clothing_item_ids": [],
            "outfit_date": outfit_data.get("outfit_date"),
            "season": outfit_data.get("season"),
            "occasion": outfit_data.get("occasion"),
            "weather_condition": outfit_data.get("weather_condition"),
            "rating": outfit_data.get("rating"),
            "is_favorite": outfit_data.get("is_favorite", False),
            "tags": [],
            "is_collage": outfit_data.get("is_collage", False),
            "canvas_layout": outfit_data.get("canvas_layout", {})
        }
        
        # Parse clothing_item_ids if provided
        if outfit_data.get("clothing_item_ids"):
            try:
                if isinstance(outfit_data["clothing_item_ids"], str):
                    prepared_data["clothing_item_ids"] = json.loads(outfit_data["clothing_item_ids"])
                else:
                    prepared_data["clothing_item_ids"] = outfit_data["clothing_item_ids"]
            except json.JSONDecodeError:
                logger.warning(f"Invalid clothing_item_ids JSON: {outfit_data['clothing_item_ids']}")
        
        # Parse tags if provided
        if outfit_data.get("tags"):
            if isinstance(outfit_data["tags"], str):
                prepared_data["tags"] = [tag.strip() for tag in outfit_data["tags"].split(",") if tag.strip()]
            else:
                prepared_data["tags"] = outfit_data["tags"]
        
        return prepared_data
    
    async def _cleanup_images(self, image_paths: List[str]) -> None:
        """Clean up uploaded images - WARNING: Only use for outfit-specific images, NOT clothing item images"""
        for path in image_paths:
            try:
                await StorageService.delete_image(path)
                logger.info(f"Cleaned up image: {path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup image {path}: {str(e)}")
    
    async def _cleanup_old_images(self, old_paths: List[str], new_paths: List[str]) -> None:
        """Clean up old images that are not in the new paths - WARNING: Only use for outfit-specific images, NOT clothing item images"""
        paths_to_cleanup = [path for path in old_paths if path not in new_paths]
        if paths_to_cleanup:
            await self._cleanup_images(paths_to_cleanup)
    
    async def _generate_outfit_images(
        self, 
        clothing_item_ids: List[str], 
        user_id: str
    ) -> List[str]:
        """Generate outfit images by combining clothing item images"""
        if not clothing_item_ids:
            logger.warning("No clothing items provided for outfit generation")
            return []
        
        try:
            logger.info(f"Generating outfit images from {len(clothing_item_ids)} clothing items")
            
            # Get clothing items from database
            clothing_items = await self._get_clothing_items(clothing_item_ids, user_id)
            if not clothing_items:
                logger.warning("No clothing items found for outfit generation")
                return []
            
            # Download and process clothing item images
            clothing_images = await self._download_clothing_images(clothing_items, user_id)
            if not clothing_images:
                logger.warning("No clothing images could be downloaded")
                return []
            
            # Generate outfit collage
            outfit_image_path = await self._create_outfit_collage(
                clothing_images, 
                clothing_items, 
                user_id
            )
            
            return [outfit_image_path] if outfit_image_path else []
            
        except Exception as e:
            logger.error(f"Error generating outfit images: {str(e)}")
            return []
    
    async def _get_clothing_items(self, item_ids: List[str], user_id: str) -> List[Dict[str, Any]]:
        """Get clothing items from database"""
        try:
            clothing_items = await DatabaseService.get_clothing_items_by_ids(item_ids, user_id)
            
            # Convert ClothingItem objects to dictionaries
            items_dict = []
            for item in clothing_items:
                items_dict.append({
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "image_path": item.image_path,
                    "seasons": item.seasons,
                    "metadata": item.metadata
                })
            
            logger.info(f"Retrieved {len(items_dict)} clothing items for outfit generation")
            return items_dict
            
        except Exception as e:
            logger.error(f"Error getting clothing items: {str(e)}")
            return []
    
    async def _download_clothing_images(
        self, 
        clothing_items: List[Dict[str, Any]], 
        _user_id: str
    ) -> List[Image.Image]:
        """Download clothing item images from storage"""
        images = []
        
        try:
            for item in clothing_items:
                image_path = item.get("image_path")
                if not image_path:
                    continue
                
                # Download image from storage
                image_data, _ = await StorageService.download_image_content(image_path)
                if image_data:
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(image_data))
                    images.append(image)
                    logger.info(f"Downloaded image for item: {item.get('name', 'Unknown')}")
                else:
                    logger.warning(f"Failed to download image for item: {item.get('name', 'Unknown')}")
            
            return images
            
        except Exception as e:
            logger.error(f"Error downloading clothing images: {str(e)}")
            return []
    
    async def _create_outfit_collage(
        self, 
        images: List[Image.Image], 
        clothing_items: List[Dict[str, Any]], 
        user_id: str
    ) -> Optional[str]:
        """Create outfit collage from clothing item images"""
        if not images:
            return None
        
        try:
            # Create a simple collage layout
            collage_width = 800
            collage_height = 600
            
            # Create base image
            collage = Image.new('RGB', (collage_width, collage_height), 'white')
            draw = ImageDraw.Draw(collage)
            
            # Simple grid layout for images
            cols = min(3, len(images))
            rows = (len(images) + cols - 1) // cols
            
            cell_width = collage_width // cols
            cell_height = collage_height // rows
            
            for i, image in enumerate(images):
                row = i // cols
                col = i % cols
                
                x = col * cell_width
                y = row * cell_height
                
                # Resize image to fit cell
                image.thumbnail((cell_width - 20, cell_height - 20), Image.Resampling.LANCZOS)
                
                # Center image in cell
                img_x = x + (cell_width - image.width) // 2
                img_y = y + (cell_height - image.height) // 2
                
                # Paste image
                collage.paste(image, (img_x, img_y))
            
            # Add outfit title
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            except OSError:
                font = ImageFont.load_default()
            
            title = f"Outfit - {len(clothing_items)} items"
            draw.text((20, 20), title, fill='black', font=font)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            collage.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)
            
            # Upload to storage
            timestamp = int(time.time() * 1000)
            filename = f"outfit_collage_{timestamp}_{user_id}.jpg"
            
            image_path = await StorageService.upload_image_unified(
                content=img_buffer.getvalue(),
                bucket_name="storage",
                filename=filename,
                user_id=user_id,
                content_type="image/jpeg"
            )
            
            if image_path:
                logger.info(f"Generated outfit collage: {image_path}")
                return image_path
            else:
                logger.error("Failed to upload generated outfit collage")
                return None
                
        except Exception as e:
            logger.error(f"Error creating outfit collage: {str(e)}")
            return None
    
    async def convert_outfits_to_frontend_format(
        self, 
        outfits: List[Outfit], 
        clothing_items: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Convert backend Outfit objects to frontend LegacyOutfit format
        This matches the conversion logic from the frontend outfitService
        """
        try:
            logger.info(f"Converting {len(outfits)} outfits to frontend format")
            
            # Create a lookup map for clothing items
            clothing_lookup = {item.id: item for item in clothing_items}
            
            frontend_outfits = []
            
            for outfit in outfits:
                # Create items from image_urls and clothing_item_ids
                items = {}
                
                # Initialize all categories as empty
                all_categories = ['tops', 'bottoms', 'shoes', 'accessories', 'outerwear']
                for category in all_categories:
                    items[category] = None
                
                # Map each image URL to its corresponding clothing item
                if outfit.image_urls and outfit.clothing_item_ids:
                    for index, image_url in enumerate(outfit.image_urls):
                        if index < len(outfit.clothing_item_ids):
                            clothing_item_id = outfit.clothing_item_ids[index]
                            clothing_item = clothing_lookup.get(clothing_item_id)
                            
                            if clothing_item:
                                # Use the actual category from the clothing item
                                category = clothing_item.category
                                items[category] = {
                                    "id": clothing_item_id,
                                    "name": clothing_item.name,
                                    "imagePath": image_url,
                                    "category": category
                                }
                            else:
                                # Fallback: use index-based category mapping
                                category = self._get_category_from_index(index)
                                items[category] = {
                                    "id": clothing_item_id,
                                    "name": f"Item {index + 1}",
                                    "imagePath": image_url,
                                    "category": category
                                }
                
                # Create frontend outfit object
                frontend_outfit = {
                    "id": outfit.id,
                    "name": outfit.name,
                    "date": outfit.outfit_date or outfit.created_at.split('T')[0],
                    "temperature": {"min": 60, "max": 80},  # Default temperature range
                    "items": items,
                    "style": outfit.tags[0] if outfit.tags else 'Casual',
                    "confidence": (outfit.rating or 3) * 20,  # Convert 1-5 rating to 0-100 confidence
                    "isGenerated": False,
                    "createdAt": outfit.created_at,
                    "isCollage": outfit.is_collage or False,
                    "canvasLayout": outfit.canvas_layout or {}
                }
                
                frontend_outfits.append(frontend_outfit)
            
            logger.info(f"Successfully converted {len(frontend_outfits)} outfits to frontend format")
            return frontend_outfits
            
        except Exception as e:
            logger.error(f"Error converting outfits to frontend format: {str(e)}")
            return []
    
    def _get_category_from_index(self, index: int) -> str:
        """Get category from index - fallback method"""
        categories = ['tops', 'bottoms', 'shoes', 'accessories', 'outerwear']
        return categories[index] if index < len(categories) else categories[index % len(categories)]


# Create singleton instance
outfit_service = OutfitService()
