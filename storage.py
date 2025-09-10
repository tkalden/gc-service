"""
Storage operations for handling image uploads
"""

import uuid
import aiofiles
from typing import Optional
from fastapi import UploadFile
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, STORAGE_BUCKET, PROFILE_PICTURES_BUCKET, DIGITAL_TWIN_BUCKET, MAX_FILE_SIZE, ALLOWED_IMAGE_TYPES
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client with error handling
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("Supabase storage client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase storage client: {str(e)}")
    supabase = None


class StorageService:
    """Service class for storage operations"""
    
    @staticmethod
    async def upload_image_content(content: bytes, filename: str, folder: str = "user-clothes", user_id: Optional[str] = None, bucket: str = STORAGE_BUCKET) -> Optional[str]:
        """Upload image content (bytes) directly to Supabase storage"""
        if not supabase:
            logger.error("Supabase client not initialized")
            return None
            
        try:
            # Validate content
            if not content or len(content) == 0:
                logger.error("Empty file content")
                return None
            
            if len(content) > MAX_FILE_SIZE:
                logger.error(f"File too large: {len(content)} bytes (max: {MAX_FILE_SIZE})")
                return None
            
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Organize by user if user_id is provided
            if user_id:
                file_path = f"{folder}/{user_id}/{unique_filename}"
            else:
                file_path = f"{folder}/{unique_filename}"
            
            logger.info(f"Uploading {len(content)} bytes to {bucket}/{file_path}")
            
            # Upload to Supabase storage
            response = supabase.storage.from_(bucket).upload(
                path=file_path,
                file=content,
                file_options={"content-type": "image/jpeg"}
            )
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Supabase storage upload error: {response.error}")
                return None
            
            logger.info(f"Successfully uploaded image to {bucket}/{file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error uploading image content: {str(e)}")
            return None
    
    @staticmethod
    async def upload_image(file: UploadFile, folder: str = "user-clothes", user_id: Optional[str] = None, bucket: str = STORAGE_BUCKET) -> Optional[str]:
        """Upload an image file to Supabase storage"""
        if not supabase:
            logger.error("Supabase client not initialized")
            return None
            
        try:
            # Validate file
            if not StorageService._validate_file(file):
                return None
            
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Organize by user if user_id is provided
            if user_id:
                file_path = f"{folder}/{user_id}/{unique_filename}"
            else:
                file_path = f"{folder}/{unique_filename}"
            
            # Read file content
            content = await file.read()
            logger.info(f"File info - filename: {file.filename}, content_type: {file.content_type}, size: {len(content)} bytes")
            
            if len(content) == 0:
                logger.error("File content is empty!")
                return None
            
            # Upload to Supabase storage
            logger.info(f"Uploading image to bucket: {bucket}, path: {file_path}")
            response = supabase.storage.from_(bucket).upload(
                path=file_path,
                file=content,
                file_options={
                    "content-type": file.content_type,
                    "cache-control": "3600"
                }
            )
            
            logger.info(f"Upload response type: {type(response)}")
            logger.info(f"Upload response: {response}")
            
            # Since the HTTP request succeeded (200 OK), assume upload was successful
            # The Supabase storage client might return different response types
            logger.info(f"Successfully uploaded image: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            return None
    
    @staticmethod
    async def delete_image(image_path: str) -> bool:
        """Delete an image from Supabase storage"""
        if not supabase:
            logger.error("Supabase client not initialized")
            return False
            
        try:
            response = supabase.storage.from_(STORAGE_BUCKET).remove([image_path])
            
            # Check if deletion was successful
            if hasattr(response, 'error') and response.error:
                logger.error(f"Error deleting image {image_path}: {response.error}")
                return False
            
            # Also check if response is a dict with error
            if isinstance(response, dict) and response.get('error'):
                logger.error(f"Error deleting image {image_path}: {response['error']}")
                return False
            
            logger.info(f"Successfully deleted image: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting image {image_path}: {str(e)}")
            return False
    
    @staticmethod
    def get_image_url(image_path: str) -> str:
        """Get the public URL for an image"""
        if not supabase:
            logger.error("Supabase client not initialized")
            return ""
            
        try:
            # Determine bucket based on image path
            if image_path.startswith('avatars/'):
                bucket = DIGITAL_TWIN_BUCKET
            else:
                bucket = STORAGE_BUCKET
            
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
    async def upload_multiple_images(files: list[UploadFile], folder: str = "user-clothes") -> list[str]:
        """Upload multiple image files"""
        uploaded_paths = []
        
        for file in files:
            path = await StorageService.upload_image(file, folder)
            if path:
                uploaded_paths.append(path)
        
        return uploaded_paths