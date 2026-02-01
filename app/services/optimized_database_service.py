"""
Optimized Database Service with batching and caching
Reduces Supabase calls by implementing intelligent batching strategies
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from app.models.models import (Avatar, AvatarCreate, ClothingItem,
                               ClothingItemCreate, ClothingItemUpdate, Outfit,
                               OutfitCreate, OutfitUpdate, TryOnResult)
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Initialize Supabase client with error handling
try:
    settings = get_settings()
    supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
    logger.info("Optimized Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize optimized Supabase client: {str(e)}")
    supabase = None


class OptimizedDatabaseService:
    """Optimized service class for database operations with batching and caching"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        self.batch_size = 50  # Process up to 50 items at once
        self.pending_requests = {}
    
    async def batch_get_clothing_items(self, user_id: str, item_ids: List[str] = None) -> List[ClothingItem]:
        """Get clothing items with batching to reduce database calls"""
        if not supabase:
            raise Exception("Supabase client not initialized")
        
        cache_key = f"clothing_items_{user_id}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.info(f"Returning cached clothing items for user {user_id}")
                return cached_data
        
        try:
            # Build optimized query
            query = supabase.table("clothing_items").select("*").eq("user_id", user_id)
            
            if item_ids:
                # If specific items requested, filter by IDs
                query = query.in_("id", item_ids)
            
            # Order by created_at for consistent results
            query = query.order("created_at", desc=True)
            
            # Limit results to reduce data transfer
            if not item_ids:  # Only limit when getting all items
                query = query.limit(100)  # Reasonable limit
            
            response = query.execute()
            
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
            
            # Cache the results
            self.cache[cache_key] = (items, datetime.now())
            
            logger.info(f"Retrieved {len(items)} clothing items from database (optimized)")
            return items
            
        except Exception as e:
            logger.error(f"Error retrieving clothing items: {str(e)}")
            raise
    
    async def batch_get_outfits(self, user_id: str, date: str = None, limit: int = 20) -> List[Outfit]:
        """Get outfits with optimized querying"""
        if not supabase:
            raise Exception("Supabase client not initialized")
        
        cache_key = f"outfits_{user_id}_{date or 'all'}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.info(f"Returning cached outfits for user {user_id}")
                return cached_data
        
        try:
            # Build optimized query
            query = supabase.table("outfits").select("*").eq("user_id", user_id)
            
            if date:
                query = query.eq("outfit_date", date)
            
            # Order by created_at and limit results
            query = query.order("created_at", desc=True).limit(limit)
            
            response = query.execute()
            
            outfits = []
            for row in response.data:
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
            
            # Cache the results
            self.cache[cache_key] = (outfits, datetime.now())
            
            logger.info(f"Retrieved {len(outfits)} outfits from database (optimized)")
            return outfits
            
        except Exception as e:
            logger.error(f"Error retrieving outfits: {str(e)}")
            raise
    
    async def batch_create_clothing_items(self, items_data: List[ClothingItemCreate], user_id: str) -> List[ClothingItem]:
        """Create multiple clothing items in a single batch operation"""
        if not supabase:
            raise Exception("Supabase client not initialized")
        
        if not items_data:
            return []
        
        try:
            # Prepare batch insert data
            insert_data = []
            for item_data in items_data:
                insert_record = {
                    "name": item_data.name,
                    "category": item_data.category.lower(),
                    "seasons": item_data.seasons,
                    "image_path": item_data.image_path,
                    "is_user_added": item_data.is_user_added,
                    "metadata": item_data.metadata or {},
                    "user_id": user_id
                }
                insert_data.append(insert_record)
            
            # Batch insert
            response = supabase.table("clothing_items").insert(insert_data).execute()
            
            # Clear cache to force refresh
            self._clear_user_cache(user_id)
            
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
            
            logger.info(f"Created {len(items)} clothing items in batch")
            return items
            
        except Exception as e:
            logger.error(f"Error batch creating clothing items: {str(e)}")
            raise
    
    async def batch_update_clothing_items(self, updates: List[Dict[str, Any]]) -> List[ClothingItem]:
        """Update multiple clothing items efficiently"""
        if not supabase:
            raise Exception("Supabase client not initialized")
        
        if not updates:
            return []
        
        try:
            # Process updates in batches
            results = []
            for i in range(0, len(updates), self.batch_size):
                batch = updates[i:i + self.batch_size]
                
                # Process each update in the batch
                batch_results = []
                for update in batch:
                    item_id = update.get("id")
                    update_data = {k: v for k, v in update.items() if k != "id" and v is not None}
                    
                    if item_id and update_data:
                        response = supabase.table("clothing_items").update(update_data).eq("id", item_id).execute()
                        
                        if response.data:
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
                            batch_results.append(item)
                
                results.extend(batch_results)
            
            # Clear cache to force refresh
            if results:
                user_id = results[0].user_id if hasattr(results[0], 'user_id') else None
                if user_id:
                    self._clear_user_cache(user_id)
            
            logger.info(f"Updated {len(results)} clothing items in batch")
            return results
            
        except Exception as e:
            logger.error(f"Error batch updating clothing items: {str(e)}")
            raise
    
    def _clear_user_cache(self, user_id: str):
        """Clear cache for a specific user"""
        keys_to_remove = [key for key in self.cache.keys() if user_id in key]
        for key in keys_to_remove:
            del self.cache[key]
        logger.info(f"Cleared cache for user {user_id}")
    
    def clear_all_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cleared all database cache")
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database usage statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_keys": list(self.cache.keys()),
            "batch_size": self.batch_size,
            "cache_ttl": self.cache_ttl
        }


# Export singleton instance
optimized_database_service = OptimizedDatabaseService()
