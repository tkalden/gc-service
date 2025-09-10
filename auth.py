"""
Authentication service for the Closet App Backend
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client for auth operations
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("Supabase auth client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase auth client: {str(e)}")
    supabase = None


class AuthService:
    """Service class for authentication operations"""
    
    @staticmethod
    async def register_user(email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user"""
        if not supabase:
            return {"success": False, "error": "Supabase client not initialized"}
            
        try:
            logger.info(f"Registering user: {email}")
            
            # Create user in Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": name or email.split('@')[0]
                    }
                }
            })
            
            if auth_response.user:
                user_data = {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "name": name or email.split('@')[0],
                    "created_at": datetime.now().isoformat()
                }
                
                logger.info(f"User registered successfully: {email}")
                return {
                    "success": True,
                    "user": user_data,
                    "access_token": auth_response.session.access_token if auth_response.session else None,
                    "message": "User registered successfully"
                }
            else:
                return {"success": False, "error": "Failed to create user"}
                
        except Exception as e:
            logger.error(f"Error registering user {email}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def login_user(email: str, password: str) -> Dict[str, Any]:
        """Login user and return access token"""
        if not supabase:
            return {"success": False, "error": "Supabase client not initialized"}
            
        try:
            logger.info(f"Logging in user: {email}")
            
            # Authenticate user
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user and auth_response.session:
                user_data = {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "name": auth_response.user.user_metadata.get('name', email.split('@')[0]),
                    "created_at": auth_response.user.created_at
                }
                
                logger.info(f"User logged in successfully: {email}")
                return {
                    "success": True,
                    "user": user_data,
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "message": "Login successful"
                }
            else:
                return {"success": False, "error": "Invalid credentials"}
                
        except Exception as e:
            logger.error(f"Error logging in user {email}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user info"""
        if not supabase:
            logger.error("Supabase client not initialized")
            return None
            
        try:
            logger.info(f"Verifying token: {token[:20]}...")
            
            # Set the token for the current session
            supabase.auth.set_session(access_token=token, refresh_token="")
            
            # Get the current user with the token
            user_response = supabase.auth.get_user(token)
            
            if user_response and user_response.user:
                logger.info(f"Token verified successfully for user: {user_response.user.email}")
                return {
                    "id": user_response.user.id,
                    "email": user_response.user.email,
                    "name": user_response.user.user_metadata.get('name', user_response.user.email.split('@')[0]),
                    "created_at": user_response.user.created_at
                }
            else:
                logger.warning("Token verification failed - no user found")
                return None
                
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            logger.error(f"Token that failed: {token[:20]}...")
            return None
    
    @staticmethod
    async def logout_user(token: str) -> Dict[str, Any]:
        """Logout user"""
        if not supabase:
            return {"success": False, "error": "Supabase client not initialized"}
            
        try:
            logger.info("Logging out user")
            
            # Sign out user
            supabase.auth.sign_out()
            
            logger.info("User logged out successfully")
            return {
                "success": True,
                "message": "Logout successful"
            }
            
        except Exception as e:
            logger.error(f"Error logging out user: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def reset_password(email: str) -> Dict[str, Any]:
        """Send password reset email"""
        if not supabase:
            return {"success": False, "error": "Supabase client not initialized"}
            
        try:
            logger.info(f"Sending password reset email to: {email}")
            
            # Send password reset email
            supabase.auth.reset_password_email(email)
            
            logger.info(f"Password reset email sent to: {email}")
            return {
                "success": True,
                "message": "Password reset email sent"
            }
            
        except Exception as e:
            logger.error(f"Error sending password reset email to {email}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[str]:
        """Extract user ID from token"""
        try:
            user_info = supabase.auth.get_user(token)
            if user_info.user:
                return user_info.user.id
            return None
        except Exception as e:
            logger.error(f"Error extracting user ID from token: {str(e)}")
            return None
    
    @staticmethod
    async def refresh_token(refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        if not supabase:
            return {"success": False, "error": "Supabase client not initialized"}
            
        try:
            logger.info("Refreshing access token")
            
            # Refresh the session
            auth_response = supabase.auth.refresh_session(refresh_token)
            
            if auth_response.session:
                user_data = {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "name": auth_response.user.user_metadata.get('name', auth_response.user.email.split('@')[0]),
                    "created_at": auth_response.user.created_at
                }
                
                logger.info("Token refreshed successfully")
                return {
                    "success": True,
                    "user": user_data,
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "message": "Token refreshed successfully"
                }
            else:
                return {"success": False, "error": "Failed to refresh token"}
                
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return {"success": False, "error": str(e)}
