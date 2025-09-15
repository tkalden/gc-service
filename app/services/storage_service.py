"""
Storage operations for handling image uploads
"""

import uuid
import aiofiles
from typing import Optional, Tuple
from fastapi import UploadFile
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, STORAGE_BUCKET, PROFILE_PICTURES_BUCKET, DIGITAL_TWIN_BUCKET, MAX_FILE_SIZE, ALLOWED_IMAGE_TYPES
import logging

logger = logging.getLogger(__name__)

# Constants
SUPABASE_CLIENT_NOT_INITIALIZED = "Supabase client not initialized"
DEFAULT_CONTENT_TYPE = "image/jpeg"

# Initialize Supabase client with error handling
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("Supabase storage client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase storage client: {str(e)}")
    supabase = None


class StorageService:
    """Service class for storage operations"""
    
    # Old helper methods removed - path generation now handled in upload_image_unified
    
    @staticmethod
    def _validate_content(content: bytes) -> bool:
        """Validate file content"""
        if not content or len(content) == 0:
            logger.error("Empty file content")
            return False
        
        if len(content) > MAX_FILE_SIZE:
            logger.error(f"File too large: {len(content)} bytes (max: {MAX_FILE_SIZE})")
            return False
        
        return True
    
    @staticmethod
    async def _upload_to_supabase(content: bytes, file_path: str, bucket: str, content_type: str = DEFAULT_CONTENT_TYPE) -> bool:
        """Upload content to Supabase storage"""
        if not supabase:
            logger.error(SUPABASE_CLIENT_NOT_INITIALIZED)
            return False
            
        try:
            logger.info(f"Uploading {len(content)} bytes to {bucket}/{file_path}")
            
            # For profile pictures, try to delete existing file first to avoid duplicates
            if bucket == PROFILE_PICTURES_BUCKET:
                try:
                    supabase.storage.from_(bucket).remove([file_path])
                    logger.info(f"Removed existing profile picture: {file_path}")
                except Exception:
                    # Ignore delete errors (file might not exist)
                    logger.info(f"No existing file to delete: {file_path}")
            
            response = supabase.storage.from_(bucket).upload(
                path=file_path,
                file=content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600"
                }
            )
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Supabase storage upload error: {response.error}")
                return False
            
            logger.info(f"Successfully uploaded image to {bucket}/{file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading to Supabase: {str(e)}")
            return False
    
    @staticmethod
    async def upload_image_unified(
        content: bytes, 
        bucket_name: str, 
        filename: Optional[str] = None, 
        user_id: Optional[str] = None,
        content_type: str = DEFAULT_CONTENT_TYPE
    ) -> Optional[str]:
        """
        Unified image upload method for all image types
        
        Args:
            content: Image content as bytes
            bucket_name: Supabase bucket name (e.g., 'clothing-image', 'digital-twin', 'profile-picture')
            filename: Optional filename (if not provided, generates uuid.jpg)
            user_id: Optional user ID for folder structure
            content_type: MIME type of the image
        
        Returns:
            Image path in Supabase storage or None if failed
        """
        if not StorageService._validate_content(content):
            return None
        
        # Generate filename if not provided
        if not filename:
            file_extension = "jpg"
            filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Generate file path
        if bucket_name == PROFILE_PICTURES_BUCKET:
            # For profile pictures, store directly in bucket root without user folder
            file_path = filename
        elif user_id:
            # For other images, use user folder structure
            file_path = f"{user_id}/{filename}"
        else:
            # When no user_id, store directly in bucket root
            file_path = filename
        
        # Upload to specified bucket
        if await StorageService._upload_to_supabase(content, file_path, bucket_name, content_type):
            logger.info(f"Successfully uploaded image to {bucket_name}/{file_path}")
            # Return just the file path without bucket name
            return file_path
        
        return None
    
    @staticmethod
    async def delete_image(image_path: str) -> bool:
        """Delete an image from Supabase storage"""
        if not supabase:
            logger.error(SUPABASE_CLIENT_NOT_INITIALIZED)
            return False
        
        bucket = StorageService._determine_bucket_from_path(image_path)
        
        # Remove bucket name from path if it's included
        actual_path = image_path
        if image_path.startswith('digital-twin/'):
            actual_path = image_path[12:]  # Remove 'digital-twin/' prefix
        elif image_path.startswith('profile-picture/'):
            actual_path = image_path[16:]  
        elif image_path.startswith('clothing-image/'):
            actual_path = image_path[15:]
        
        # Remove any leading slash that might have been created
        if actual_path.startswith('/'):
            actual_path = actual_path[1:]
            
        try:
            logger.info(f"Deleting image: '{image_path}' -> actual_path: '{actual_path}' from bucket: {bucket}")
            response = supabase.storage.from_(bucket).remove([actual_path])
            
            # Check if deletion was successful
            if hasattr(response, 'error') and response.error:
                logger.error(f"Error deleting image {image_path}: {response.error}")
                return False
            
            # Also check if response is a dict with error
            if isinstance(response, dict) and response.get('error'):
                logger.error(f"Error deleting image {image_path}: {response['error']}")
                return False
            
            logger.info(f"Successfully deleted image: {actual_path} from bucket: {bucket}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting image {image_path}: {str(e)}")
            return False
    
    @staticmethod
    def get_image_url(image_path: str) -> str:
        """Get the public URL for an image"""
        if not supabase:
            logger.error(SUPABASE_CLIENT_NOT_INITIALIZED)
            return ""
        
        bucket = StorageService._determine_bucket_from_path(image_path)
            
        try:
            logger.info(f"Getting image URL for path: '{image_path}' from bucket: {bucket}")
            
            response = supabase.storage.from_(bucket).get_public_url(image_path)
            logger.info(f"Image URL response for {image_path} (bucket: {bucket}): {response} (type: {type(response)})")
            
            # Handle different response types
            if isinstance(response, str):
                return response
            elif hasattr(response, 'public_url'):
                return response.public_url
            elif isinstance(response, dict) and 'public_url' in response:
                return response['public_url']
            else:
                logger.error(f"Unexpected response type for image URL: {type(response)}")
                return ""
                
        except Exception as e:
            logger.error(f"Error getting image URL for {image_path}: {str(e)}")
            return ""
    
    # Old profile picture methods removed - use upload_image_unified instead

    @staticmethod
    def _get_content_type_from_path(image_path: str) -> str:
        """Determine content type from file extension"""
        if image_path.lower().endswith('.png'):
            return "image/png"
        elif image_path.lower().endswith('.webp'):
            return "image/webp"
        else:
            return DEFAULT_CONTENT_TYPE

    @staticmethod
    async def download_image_content(image_path: str) -> Tuple[bytes, str]:
        """Download image content directly using service key"""
        if not supabase:
            logger.error(SUPABASE_CLIENT_NOT_INITIALIZED)
            return b"", ""
        
        # Determine bucket and actual path
        bucket = None
        actual_path = image_path
        
        # Check if path includes bucket name (for backward compatibility)
        if image_path.startswith('digital-twin/'):
            bucket = DIGITAL_TWIN_BUCKET
            actual_path = image_path[12:]  # Remove 'digital-twin/' prefix
        elif image_path.startswith('profile-picture/'):
            bucket = PROFILE_PICTURES_BUCKET
            actual_path = image_path[16:]  
        elif image_path.startswith('clothing-image/'):
            bucket = STORAGE_BUCKET
            actual_path = image_path[15:]
        else:
            # Path doesn't include bucket name, try to determine from context
            # For avatar images (original/processed), assume digital-twin bucket
            if 'original' in image_path.lower() or 'processed' in image_path.lower():
                bucket = DIGITAL_TWIN_BUCKET
            elif 'avatar' in image_path.lower():
                bucket = DIGITAL_TWIN_BUCKET
            else:
                bucket = STORAGE_BUCKET  # Default to clothing images
        
        # Remove any leading slash that might have been created
        if actual_path.startswith('/'):
            actual_path = actual_path[1:]
            
        try:
            logger.info(f"Downloading image content for path: '{image_path}' -> actual_path: '{actual_path}' from bucket: {bucket}")
            
            response = supabase.storage.from_(bucket).download(actual_path)
            logger.info(f"Download response type: {type(response)}")
            
            if isinstance(response, bytes):
                content_type = StorageService._get_content_type_from_path(actual_path)
                logger.info(f"Successfully downloaded {len(response)} bytes of image content")
                return response, content_type
            else:
                logger.error(f"Unexpected response type for image download: {type(response)}")
                return b"", ""
                
        except Exception as e:
            logger.error(f"Error downloading image content for {image_path} (actual_path: {actual_path}): {str(e)}")
            return b"", ""
    
    @staticmethod
    def _validate_file(file: UploadFile) -> bool:
        """Validate uploaded file"""
        try:
            # Check file size
            if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
                logger.error(f"File too large: {file.size} bytes (max: {MAX_FILE_SIZE})")
                return False
            
            # Check content type
            if file.content_type not in ALLOWED_IMAGE_TYPES:
                logger.error(f"Invalid file type: {file.content_type}")
                return False
            
            # Check filename
            if not file.filename:
                logger.error("No filename provided")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return False

    @staticmethod
    def _determine_bucket_from_path(image_path: str) -> str:
        """Determine the appropriate bucket based on the image path"""
        if image_path.startswith('digital-twin/'):
            return DIGITAL_TWIN_BUCKET
        elif image_path.startswith('profile-picture/'):
            return PROFILE_PICTURES_BUCKET
        elif image_path.startswith('clothing-image/'):
            return STORAGE_BUCKET
        else:
            # Fallback: assume it's a clothing image if no bucket prefix
            logger.warning(f"No bucket prefix found in path: {image_path}, defaulting to clothing-image")
            return STORAGE_BUCKET   
    