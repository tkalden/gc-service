"""
Pydantic models for the Closet App API
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class ClothingItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., pattern="^(tops|bottoms|shoes|accessories|dresses|outerwear|Tops|Bottoms|Shoes|Accessories|Dresses|Outerwear)$")
    seasons: List[str] = Field(..., min_items=1)
    image_path: Optional[str] = None
    is_user_added: bool = True
    metadata: Optional[dict] = None


class ClothingItemCreate(ClothingItemBase):
    pass


class ClothingItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, pattern="^(tops|bottoms|shoes|accessories|dresses|outerwear|Tops|Bottoms|Shoes|Accessories|Dresses|Outerwear)$")
    seasons: Optional[List[str]] = Field(None, min_items=1)
    metadata: Optional[dict] = None


class ClothingItem(ClothingItemBase):
    id: str
    image_path: Optional[str] = None
    added_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClothingItemResponse(BaseModel):
    success: bool
    data: Optional[ClothingItem] = None
    message: Optional[str] = None


class ClothingItemsResponse(BaseModel):
    success: bool
    data: List[ClothingItem] = []
    count: int = 0
    message: Optional[str] = None


class ImageUploadResponse(BaseModel):
    success: bool
    image_path: Optional[str] = None
    message: Optional[str] = None


class Base64UploadRequest(BaseModel):
    file_data: str = Field(..., description="Base64 encoded image data")
    filename: str = Field(..., description="Name of the file")
    folder: str = Field(default="user-clothes", description="Folder to store the image")
    content_type: str = Field(default="image/jpeg", description="MIME type of the image")


class DeleteResponse(BaseModel):
    success: bool
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None


# Authentication Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: datetime


class AuthResponse(BaseModel):
    success: bool
    user: Optional[UserResponse] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    message: Optional[str] = None


class TokenResponse(BaseModel):
    success: bool
    access_token: Optional[str] = None
    user: Optional[UserResponse] = None
    message: Optional[str] = None


# Digital Twin Avatar Models
class AvatarCreate(BaseModel):
    original_image_path: str = Field(..., description="Path to the original avatar image")
    
    
class Avatar(BaseModel):
    id: str
    user_id: str
    original_image_path: str
    processed_image_path: Optional[str] = None
    pose_keypoints: Optional[Dict] = Field(default=None, description="MediaPipe pose keypoints data")
    body_segments: Optional[Dict] = Field(default=None, description="Body segmentation data")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Pose detection confidence")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AvatarResponse(BaseModel):
    success: bool
    data: Optional[Avatar] = None
    message: Optional[str] = None


class TryOnRequest(BaseModel):
    avatar_id: str = Field(..., description="ID of the user's avatar")
    clothing_item_id: str = Field(..., description="ID of the clothing item to try on")
    pose_adjustment: Optional[Dict] = Field(default=None, description="Optional pose adjustments")


class TryOnResult(BaseModel):
    id: str
    user_id: str
    avatar_id: str
    clothing_item_id: str
    result_image_path: str
    confidence_score: float = Field(ge=0.0, le=1.0, description="Try-on quality confidence")
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")
    created_at: datetime
    
    class Config:
        from_attributes = True


class TryOnResponse(BaseModel):
    success: bool
    data: Optional[TryOnResult] = None
    message: Optional[str] = None


# Outfit Models
class OutfitBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the outfit")
    description: Optional[str] = Field(None, max_length=500, description="Description of the outfit")
    image_urls: List[str] = Field(default=[], max_items=10, description="List of image URLs for the outfit")
    clothing_item_ids: Optional[List[str]] = Field(default=[], description="List of clothing item IDs used in this outfit")
    outfit_date: str = Field(..., description="Date when the outfit was worn (YYYY-MM-DD)")
    season: Optional[str] = Field(None, pattern="^(spring|summer|fall|winter|all-season)$", description="Season for this outfit")
    occasion: Optional[str] = Field(None, max_length=50, description="Occasion or event type")
    weather_condition: Optional[str] = Field(None, max_length=50, description="Weather condition")
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating from 1 to 5 stars")
    is_favorite: bool = Field(default=False, description="Whether this outfit is marked as favorite")
    tags: Optional[List[str]] = Field(default=[], max_items=20, description="Tags for search and filtering")
    is_collage: bool = Field(default=False, description="Whether this outfit has custom positioning (collage mode)")
    canvas_layout: Optional[Dict[str, Any]] = Field(default={}, description="JSON object storing custom positions and sizes for each clothing item category")


class OutfitCreate(OutfitBase):
    pass


class OutfitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    image_urls: Optional[List[str]] = Field(None, min_items=1, max_items=10)
    clothing_item_ids: Optional[List[str]] = None
    outfit_date: Optional[str] = None
    season: Optional[str] = Field(None, pattern="^(spring|summer|fall|winter|all-season)$")
    occasion: Optional[str] = Field(None, max_length=50)
    weather_condition: Optional[str] = Field(None, max_length=50)
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_favorite: Optional[bool] = None
    tags: Optional[List[str]] = Field(None, max_items=20)
    is_collage: Optional[bool] = None
    canvas_layout: Optional[Dict[str, Any]] = None


class Outfit(OutfitBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OutfitResponse(BaseModel):
    success: bool
    data: Optional[Outfit] = None
    message: Optional[str] = None


class OutfitsResponse(BaseModel):
    success: bool
    data: List[Outfit] = []
    count: int = 0
    message: Optional[str] = None


class OutfitFilterRequest(BaseModel):
    season: Optional[str] = Field(None, pattern="^(spring|summer|fall|winter|all-season)$")
    occasion: Optional[str] = None
    weather_condition: Optional[str] = None
    is_favorite: Optional[bool] = None
    tags: Optional[List[str]] = None
    start_date: Optional[str] = Field(None, description="Start date for filtering (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for filtering (YYYY-MM-DD)")
    min_rating: Optional[int] = Field(None, ge=1, le=5)
    limit: Optional[int] = Field(default=20, ge=1, le=100)
    offset: Optional[int] = Field(default=0, ge=0)