"""
Admin router - Only used endpoints
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.logging import get_logger
from app.middleware.middleware import get_current_user_id

# Admin endpoints - removed AI processing endpoints
# AI endpoints moved to /upload folder where they belong

logger = get_logger(__name__)
router = APIRouter()

# Admin endpoints are now clean - AI processing moved to /upload folder