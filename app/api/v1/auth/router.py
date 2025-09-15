"""
Authentication router
"""

from fastapi import APIRouter, Depends, HTTPException, Form
from app.core.logging import get_logger
from app.core.exceptions import AuthenticationException
from app.services.auth_service import AuthService
from app.models.models import UserRegister, UserLogin, AuthResponse, TokenResponse
from app.middleware.middleware import get_current_user, get_current_user_id

logger = get_logger(__name__)
router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register_user(user_data: UserRegister):
    """Register a new user"""
    try:
        result = await AuthService.register_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name
        )
        
        if result["success"]:
            return AuthResponse(
                success=True,
                user=result["user"],
                access_token=result["access_token"],
                message=result["message"]
            )
        else:
            raise AuthenticationException(result["error"])
            
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error(f"Error in register endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login_user(user_data: UserLogin):
    """Login user"""
    try:
        result = await AuthService.login_user(
            email=user_data.email,
            password=user_data.password
        )
        
        if result["success"]:
            return AuthResponse(
                success=True,
                user=result["user"],
                access_token=result["access_token"],
                refresh_token=result.get("refresh_token"),
                message=result["message"]
            )
        else:
            raise AuthenticationException(result["error"])
            
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error(f"Error in login endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout_user(current_user: dict = Depends(get_current_user)):
    """Logout current user"""
    try:
        result = await AuthService.logout_user(current_user["id"])
        
        if result["success"]:
            return {"success": True, "message": result["message"]}
        else:
            raise AuthenticationException(result["error"])
            
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error(f"Error in logout endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=TokenResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return TokenResponse(
        success=True,
        user=current_user,
        message="User information retrieved successfully"
    )


@router.post("/reset-password")
async def reset_password(email: str):
    """Send password reset email"""
    try:
        result = await AuthService.reset_password(email)
        
        if result["success"]:
            return {"success": True, "message": result["message"]}
        else:
            raise AuthenticationException(result["error"])
            
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error(f"Error in reset password endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str = Form(...)):
    """Refresh access token"""
    try:
        result = await AuthService.refresh_token(refresh_token)
        
        if result["success"]:
            return AuthResponse(
                success=True,
                user=result["user"],
                access_token=result["access_token"],
                message=result["message"]
            )
        else:
            raise AuthenticationException(result["error"])
            
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error(f"Error in refresh token endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
