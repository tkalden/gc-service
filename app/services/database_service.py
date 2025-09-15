"""
Database operations using Supabase
"""

from typing import List, Optional
from supabase import create_client, Client
from config.settings import get_settings
from models import ClothingItem, ClothingItemCreate, ClothingItemUpdate, Avatar, AvatarCreate, TryOnResult, Outfit, OutfitCreate, OutfitUpdate
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client with error handling
try:
    settings = get_settings()
    supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    supabase = None


class DatabaseService:
    """Service class for database operations"""
    
    @staticmethod
    async def get_all_clothing_items(user_id: str) -> List[ClothingItem]:
        """Get all clothing items from the database"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            response = supabase.table("clothing_items").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            
            items = []
            for row in response.data:
                item = ClothingItem(
                    id=row["id"],
                    name=row["name"],
                    category=row["category"],
                    seasons=row["seasons"],
                    image_path=row.get("image_path"),
                    is_user_added=row["is_user_added"],
                    added_date=row["added_date"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata=row.get("metadata", {})
                )
                items.append(item)
            
            logger.info(f"Retrieved {len(items)} clothing items from database")
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving clothing items: {str(e)}")
            raise
    
    @staticmethod
    async def get_clothing_item_by_id(item_id: str) -> Optional[ClothingItem]:
        """Get a specific clothing item by ID"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            response = supabase.table("clothing_items").select("*").eq("id", item_id).execute()
            
            if not response.data:
                return None
            
            row = response.data[0]
            item = ClothingItem(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                seasons=row["seasons"],
                image_path=row.get("image_path"),
                is_user_added=row["is_user_added"],
                added_date=row["added_date"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=row.get("metadata", {})
            )
            
            return item
            
        except Exception as e:
            logger.error(f"Error retrieving clothing item {item_id}: {str(e)}")
            raise
    
    @staticmethod
    async def get_clothing_items_by_ids(item_ids: List[str], user_id: str) -> List[ClothingItem]:
        """Get multiple clothing items by their IDs"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        if not item_ids:
            return []
            
        try:
            response = supabase.table("clothing_items").select("*").in_("id", item_ids).eq("user_id", user_id).execute()
            
            items = []
            for row in response.data:
                item = ClothingItem(
                    id=row["id"],
                    name=row["name"],
                    category=row["category"],
                    seasons=row["seasons"],
                    image_path=row.get("image_path"),
                    is_user_added=row["is_user_added"],
                    added_date=row["added_date"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata=row.get("metadata", {})
                )
                items.append(item)
            
            logger.info(f"Retrieved {len(items)} clothing items by IDs from database")
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving clothing items by IDs: {str(e)}")
            raise
    
    @staticmethod
    async def create_clothing_item(item_data: ClothingItemCreate, user_id: str) -> ClothingItem:
        """Create a new clothing item"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            # Prepare data for insertion
            insert_data = {
                "name": item_data.name,
                "category": item_data.category.lower(),
                "seasons": item_data.seasons,
                "image_path": item_data.image_path,
                "is_user_added": item_data.is_user_added,
                "metadata": item_data.metadata or {},
                "user_id": user_id
            }
            
            logger.info(f"Creating clothing item with data: {insert_data}")
            logger.info(f"Image path value: {item_data.image_path}")
            
            response = supabase.table("clothing_items").insert(insert_data).execute()
            
            if not response.data:
                raise Exception("Failed to create clothing item")
            
            row = response.data[0]
            logger.info(f"Database response row: {row}")
            logger.info(f"Image path in response: {row.get('image_path')}")
            item = ClothingItem(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                seasons=row["seasons"],
                image_path=row.get("image_path"),
                is_user_added=row["is_user_added"],
                added_date=row["added_date"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=row.get("metadata", {})
            )
            
            logger.info(f"Created clothing item: {item.name} (ID: {item.id})")
            return item
            
        except Exception as e:
            logger.error(f"Error creating clothing item: {str(e)}")
            raise
    
    @staticmethod
    async def update_clothing_item(item_id: str, update_data: ClothingItemUpdate) -> Optional[ClothingItem]:
        """Update an existing clothing item"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            # Prepare update data
            update_dict = {}
            if update_data.name is not None:
                update_dict["name"] = update_data.name
            if update_data.category is not None:
                update_dict["category"] = update_data.category.lower()
            if update_data.seasons is not None:
                update_dict["seasons"] = update_data.seasons
            if update_data.metadata is not None:
                update_dict["metadata"] = update_data.metadata
            
            if not update_dict:
                # No updates to make
                return await DatabaseService.get_clothing_item_by_id(item_id)
            
            response = supabase.table("clothing_items").update(update_dict).eq("id", item_id).execute()
            
            if not response.data:
                return None
            
            row = response.data[0]
            item = ClothingItem(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                seasons=row["seasons"],
                image_path=row.get("image_path"),
                is_user_added=row["is_user_added"],
                added_date=row["added_date"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=row.get("metadata", {})
            )
            
            logger.info(f"Updated clothing item: {item.name} (ID: {item.id})")
            return item
            
        except Exception as e:
            logger.error(f"Error updating clothing item {item_id}: {str(e)}")
            raise
    
    @staticmethod
    async def delete_clothing_item(item_id: str) -> bool:
        """Delete a clothing item"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            response = supabase.table("clothing_items").delete().eq("id", item_id).execute()
            
            success = len(response.data) > 0
            if success:
                logger.info(f"Deleted clothing item with ID: {item_id}")
            else:
                logger.warning(f"Clothing item with ID {item_id} not found")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting clothing item {item_id}: {str(e)}")
            raise
    
    @staticmethod
    async def update_clothing_item_image(item_id: str, image_path: str) -> Optional[ClothingItem]:
        """Update the image path for a clothing item"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            response = supabase.table("clothing_items").update({"image_path": image_path}).eq("id", item_id).execute()
            
            if not response.data:
                return None
            
            row = response.data[0]
            item = ClothingItem(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                seasons=row["seasons"],
                image_path=row.get("image_path"),
                is_user_added=row["is_user_added"],
                added_date=row["added_date"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=row.get("metadata", {})
            )
            
            logger.info(f"Updated image path for clothing item: {item.name} (ID: {item.id})")
            return item
            
        except Exception as e:
            logger.error(f"Error updating image path for clothing item {item_id}: {str(e)}")
            raise
    
    # Avatar Database Operations
    
    @staticmethod
    async def create_avatar(avatar_data: dict, user_id: str) -> Optional[Avatar]:
        """Create a new avatar record"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            import uuid
            from datetime import datetime
            
            avatar_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            avatar_record = {
                "id": avatar_id,
                "user_id": user_id,
                "original_image_path": avatar_data.get("original_image_path", ""),
                "processed_image_path": avatar_data.get("processed_image_path"),
                "pose_keypoints": avatar_data.get("pose_keypoints"),
                "body_segments": avatar_data.get("body_segments"),
                "confidence_score": avatar_data.get("confidence_score", 0.0),
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat()
            }
            
            response = supabase.table("avatars").insert(avatar_record).execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return Avatar(
                    id=row["id"],
                    user_id=row["user_id"],
                    original_image_path=row["original_image_path"],
                    processed_image_path=row.get("processed_image_path"),
                    pose_keypoints=row.get("pose_keypoints"),
                    body_segments=row.get("body_segments"),
                    confidence_score=row.get("confidence_score", 0.0),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            else:
                logger.error("No data returned from avatar creation")
                return None
                
        except Exception as e:
            logger.error(f"Error creating avatar: {str(e)}")
            raise
    
    @staticmethod
    async def upsert_avatar(avatar_data: dict, user_id: str) -> Optional[Avatar]:
        """Create or update avatar record (ensures only one avatar per user)"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            import uuid
            from datetime import datetime
            
            current_time = datetime.utcnow()
            
            # Check if user already has an avatar
            existing_avatar = await DatabaseService.get_user_avatar(user_id)
            
            if existing_avatar:
                # Update existing avatar
                logger.info(f"Updating existing avatar for user: {user_id}")
                
                update_data = {
                    "original_image_path": avatar_data.get("original_image_path", ""),
                    "processed_image_path": avatar_data.get("processed_image_path"),
                    "pose_keypoints": avatar_data.get("pose_keypoints"),
                    "body_segments": avatar_data.get("body_segments"),
                    "confidence_score": avatar_data.get("confidence_score", 0.0),
                    "updated_at": current_time.isoformat()
                }
                
                response = supabase.table("avatars").update(update_data).eq("user_id", user_id).execute()
                
                if response.data and len(response.data) > 0:
                    row = response.data[0]
                    return Avatar(
                        id=row["id"],
                        user_id=row["user_id"],
                        original_image_path=row["original_image_path"],
                        processed_image_path=row.get("processed_image_path"),
                        pose_keypoints=row.get("pose_keypoints"),
                        body_segments=row.get("body_segments"),
                        confidence_score=row.get("confidence_score", 0.0),
                        created_at=row["created_at"],
                        updated_at=row["updated_at"]
                    )
                else:
                    logger.error("No data returned from avatar update")
                    return None
            else:
                # Create new avatar
                logger.info(f"Creating new avatar for user: {user_id}")
                return await DatabaseService.create_avatar(avatar_data, user_id)
                
        except Exception as e:
            logger.error(f"Error upserting avatar: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_avatar(user_id: str) -> Optional[Avatar]:
        """Get user's avatar (latest one)"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            response = supabase.table("avatars").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return Avatar(
                    id=row["id"],
                    user_id=row["user_id"],
                    original_image_path=row["original_image_path"],
                    processed_image_path=row.get("processed_image_path"),
                    pose_keypoints=row.get("pose_keypoints"),
                    body_segments=row.get("body_segments"),
                    confidence_score=row.get("confidence_score", 0.0),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting user avatar: {str(e)}")
            raise
    
    @staticmethod
    async def delete_avatar(user_id: str) -> bool:
        """Delete user's avatar record"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            supabase.table("avatars").delete().eq("user_id", user_id).execute()
            logger.info(f"Deleted avatar record for user: {user_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error deleting user avatar: {str(e)}")
            raise
    
    @staticmethod
    async def get_avatar_by_id(avatar_id: str) -> Optional[Avatar]:
        """Get avatar by ID"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            response = supabase.table("avatars").select("*").eq("id", avatar_id).execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return Avatar(
                    id=row["id"],
                    user_id=row["user_id"],
                    original_image_path=row["original_image_path"],
                    processed_image_path=row.get("processed_image_path"),
                    pose_keypoints=row.get("pose_keypoints"),
                    body_segments=row.get("body_segments"),
                    confidence_score=row.get("confidence_score", 0.0),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting avatar by ID: {str(e)}")
            raise
    
    # Try-On Results Database Operations
    
    @staticmethod
    async def create_tryon_result(result_data: dict) -> Optional[TryOnResult]:
        """Create a new try-on result record"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            import uuid
            from datetime import datetime
            
            result_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            result_record = {
                "id": result_id,
                "user_id": result_data["user_id"],
                "avatar_id": result_data["avatar_id"],
                "clothing_item_id": result_data["clothing_item_id"],
                "result_image_path": result_data["result_image_path"],
                "confidence_score": result_data.get("confidence_score", 0.0),
                "processing_time": result_data.get("processing_time"),
                "created_at": current_time.isoformat()
            }
            
            response = supabase.table("tryon_results").insert(result_record).execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return TryOnResult(
                    id=row["id"],
                    user_id=row["user_id"],
                    avatar_id=row["avatar_id"],
                    clothing_item_id=row["clothing_item_id"],
                    result_image_path=row["result_image_path"],
                    confidence_score=row.get("confidence_score", 0.0),
                    processing_time=row.get("processing_time"),
                    created_at=row["created_at"]
                )
            else:
                logger.error("No data returned from try-on result creation")
                return None
                
        except Exception as e:
            logger.error(f"Error creating try-on result: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_tryon_results(user_id: str, limit: int = 20) -> List[TryOnResult]:
        """Get user's try-on results"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            response = supabase.table("tryon_results").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            
            results = []
            if response.data:
                for row in response.data:
                    result = TryOnResult(
                        id=row["id"],
                        user_id=row["user_id"],
                        avatar_id=row["avatar_id"],
                        clothing_item_id=row["clothing_item_id"],
                        result_image_path=row["result_image_path"],
                        confidence_score=row.get("confidence_score", 0.0),
                        processing_time=row.get("processing_time"),
                        created_at=row["created_at"]
                    )
                    results.append(result)
            
            return results
                
        except Exception as e:
            logger.error(f"Error getting user try-on results: {str(e)}")
            raise
    
    # Outfit Database Operations
    
    @staticmethod
    async def create_outfit(outfit_data: dict, user_id: str) -> Optional[Outfit]:
        """Create a new outfit record"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            import uuid
            from datetime import datetime
            
            outfit_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            outfit_record = {
                "id": outfit_id,
                "user_id": user_id,
                "name": outfit_data.get("name", "My Outfit"),
                "description": outfit_data.get("description"),
                "image_urls": outfit_data.get("image_urls", []),
                "clothing_item_ids": outfit_data.get("clothing_item_ids", []),
                "outfit_date": outfit_data.get("outfit_date"),
                "season": outfit_data.get("season"),
                "occasion": outfit_data.get("occasion"),
                "weather_condition": outfit_data.get("weather_condition"),
                "rating": outfit_data.get("rating"),
                "is_favorite": outfit_data.get("is_favorite", False),
                "tags": outfit_data.get("tags", []),
                "is_collage": outfit_data.get("is_collage", False),
                "canvas_layout": outfit_data.get("canvas_layout", {}),
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat()
            }
            
            response = supabase.table("outfits").insert(outfit_record).execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return Outfit(
                    id=row["id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    description=row.get("description"),
                    image_urls=row.get("image_urls", []),
                    clothing_item_ids=row.get("clothing_item_ids", []),
                    outfit_date=row.get("outfit_date"),
                    season=row.get("season"),
                    occasion=row.get("occasion"),
                    weather_condition=row.get("weather_condition"),
                    rating=row.get("rating"),
                    is_favorite=row.get("is_favorite", False),
                    tags=row.get("tags", []),
                    is_collage=row.get("is_collage", False),
                    canvas_layout=row.get("canvas_layout", {}),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            else:
                logger.error("No data returned from outfit creation")
                return None
                
        except Exception as e:
            logger.error(f"Error creating outfit: {str(e)}")
            raise
    
    @staticmethod
    async def get_outfit_by_id(outfit_id: str, user_id: str) -> Optional[Outfit]:
        """Get outfit by ID (must belong to user)"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            response = supabase.table("outfits").select("*").eq("id", outfit_id).eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return Outfit(
                    id=row["id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    description=row.get("description"),
                    image_urls=row.get("image_urls", []),
                    clothing_item_ids=row.get("clothing_item_ids", []),
                    outfit_date=row.get("outfit_date"),
                    season=row.get("season"),
                    occasion=row.get("occasion"),
                    weather_condition=row.get("weather_condition"),
                    rating=row.get("rating"),
                    is_favorite=row.get("is_favorite", False),
                    tags=row.get("tags", []),
                    is_collage=row.get("is_collage", False),
                    canvas_layout=row.get("canvas_layout", {}),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting outfit by ID: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_outfits(user_id: str, limit: int = 20, offset: int = 0, filters: dict = None) -> List[Outfit]:
        """Get user's outfits with optional filtering"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            query = supabase.table("outfits").select("*").eq("user_id", user_id)
            
            # Apply filters if provided
            if filters:
                if filters.get("season"):
                    query = query.eq("season", filters["season"])
                if filters.get("occasion"):
                    query = query.eq("occasion", filters["occasion"])
                if filters.get("weather_condition"):
                    query = query.eq("weather_condition", filters["weather_condition"])
                if filters.get("is_favorite") is not None:
                    query = query.eq("is_favorite", filters["is_favorite"])
                if filters.get("min_rating"):
                    query = query.gte("rating", filters["min_rating"])
                if filters.get("start_date"):
                    query = query.gte("outfit_date", filters["start_date"])
                if filters.get("end_date"):
                    query = query.lte("outfit_date", filters["end_date"])
                if filters.get("tags"):
                    # Use JSONB contains operator for tags
                    for tag in filters["tags"]:
                        query = query.contains("tags", [tag])
            
            # Apply pagination and ordering
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            response = query.execute()
            
            outfits = []
            if response.data:
                for row in response.data:
                    logger.info(f"Raw outfit data from DB: {row}")
                    outfit = Outfit(
                        id=row["id"],
                        user_id=row["user_id"],
                        name=row["name"],
                        description=row.get("description"),
                        image_urls=row.get("image_urls", []),
                        clothing_item_ids=row.get("clothing_item_ids", []),
                        outfit_date=row.get("outfit_date"),
                        season=row.get("season"),
                        occasion=row.get("occasion"),
                        weather_condition=row.get("weather_condition"),
                        rating=row.get("rating"),
                        is_favorite=row.get("is_favorite", False),
                        tags=row.get("tags", []),
                        is_collage=row.get("is_collage", False),
                        canvas_layout=row.get("canvas_layout", {}),
                        created_at=row["created_at"],
                        updated_at=row["updated_at"]
                    )
                    outfits.append(outfit)
            
            return outfits
            
        except Exception as e:
            logger.error(f"Error getting user outfits: {str(e)}")
            raise
    
    @staticmethod
    async def update_outfit(outfit_id: str, outfit_data: dict, user_id: str) -> Optional[Outfit]:
        """Update outfit record"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            from datetime import datetime
            
            current_time = datetime.utcnow()
            
            # Prepare update data (only include non-None values)
            update_data = {"updated_at": current_time.isoformat()}
            
            for field in ["name", "description", "image_urls", "clothing_item_ids", 
                         "outfit_date", "season", "occasion", "weather_condition", 
                         "rating", "is_favorite", "tags", "is_collage", "canvas_layout"]:
                if field in outfit_data and outfit_data[field] is not None:
                    update_data[field] = outfit_data[field]
            
            response = supabase.table("outfits").update(update_data).eq("id", outfit_id).eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return Outfit(
                    id=row["id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    description=row.get("description"),
                    image_urls=row.get("image_urls", []),
                    clothing_item_ids=row.get("clothing_item_ids", []),
                    outfit_date=row.get("outfit_date"),
                    season=row.get("season"),
                    occasion=row.get("occasion"),
                    weather_condition=row.get("weather_condition"),
                    rating=row.get("rating"),
                    is_favorite=row.get("is_favorite", False),
                    tags=row.get("tags", []),
                    is_collage=row.get("is_collage", False),
                    canvas_layout=row.get("canvas_layout", {}),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error updating outfit: {str(e)}")
            raise
    
    @staticmethod
    async def delete_outfit(outfit_id: str, user_id: str) -> bool:
        """Delete outfit record"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            response = supabase.table("outfits").delete().eq("id", outfit_id).eq("user_id", user_id).execute()
            logger.info(f"Deleted outfit {outfit_id} for user: {user_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error deleting outfit: {str(e)}")
            raise
    
    @staticmethod
    async def get_outfit_count(user_id: str, filters: dict = None) -> int:
        """Get count of user's outfits with optional filtering"""
        if not supabase:
            raise Exception("Supabase client not initialized")
            
        try:
            query = supabase.table("outfits").select("id", count="exact").eq("user_id", user_id)
            
            # Apply filters if provided
            if filters:
                if filters.get("season"):
                    query = query.eq("season", filters["season"])
                if filters.get("occasion"):
                    query = query.eq("occasion", filters["occasion"])
                if filters.get("weather_condition"):
                    query = query.eq("weather_condition", filters["weather_condition"])
                if filters.get("is_favorite") is not None:
                    query = query.eq("is_favorite", filters["is_favorite"])
                if filters.get("min_rating"):
                    query = query.gte("rating", filters["min_rating"])
                if filters.get("start_date"):
                    query = query.gte("outfit_date", filters["start_date"])
                if filters.get("end_date"):
                    query = query.lte("outfit_date", filters["end_date"])
                if filters.get("tags"):
                    for tag in filters["tags"]:
                        query = query.contains("tags", [tag])
            
            response = query.execute()
            return response.count if response.count is not None else 0
            
        except Exception as e:
            logger.error(f"Error getting outfit count: {str(e)}")
            raise
    