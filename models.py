"""
Pydantic models for the Closet App API
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class ClothingItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., pattern="^(tops|bottoms|shoes|accessories|dresses|outerwear)$")
    seasons: List[str] = Field(..., min_items=1)
    image_path: Optional[str] = None
    is_user_added: bool = True
    metadata: Optional[dict] = None


class ClothingItemCreate(ClothingItemBase):
    pass


class ClothingItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, pattern="^(tops|bottoms|shoes|accessories|dresses|outerwear)$")
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