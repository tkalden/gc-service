"""
Authentication middleware for the Closet App Backend
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging
from auth import AuthService

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme with auto_error=False to handle errors ourselves
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user
    """
    try:
        if credentials:
            logger.info(f"Credentials scheme: {credentials.scheme}")
            logger.info(f"Credentials token preview: {credentials.credentials[:20]}...")
        
        if not credentials:
            logger.warning("No credentials provided")
            logger.warning("This means the HTTPBearer security scheme did not find an Authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication credentials provided",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials
        logger.info(f"Authentication attempt with token: {token[:20]}...")
        # Verify token with Supabase
        user_info = await AuthService.verify_token(token)
        
        if not user_info:
            logger.warning("Invalid or expired token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Authenticated user: {user_info['email']}")
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in authentication middleware: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Dependency to get current user ID
    """
    user = await get_current_user(credentials)
    return user["id"]

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns user if authenticated, None otherwise
    """
    try:
        if not credentials:
            return None
        return await get_current_user(credentials)
    except HTTPException:
        return None
