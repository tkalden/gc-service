"""
Background removal service using rembg (free local processing)
"""
import os
import tempfile
import base64
from typing import Optional, Tuple
from fastapi import HTTPException
import logging
from PIL import Image
import io
import requests

logger = logging.getLogger(__name__)

# Try to import rembg, handle if not installed
try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
    logger.info("rembg library loaded successfully")
except ImportError:
    REMBG_AVAILABLE = False
    logger.warning("rembg library not installed. Install with: pip install rembg")

class BackgroundRemovalService:
    def __init__(self):
        self.session = None
        if REMBG_AVAILABLE:
            try:
                # Initialize rembg session with u2net model (good for general objects)
                self.session = new_session('u2net')
                logger.info("rembg session initialized with u2net model")
            except Exception as e:
                logger.error(f"Failed to initialize rembg session: {e}")
                self.session = None
    
    def is_configured(self) -> bool:
        """Check if the background removal service is available"""
        return REMBG_AVAILABLE and self.session is not None
    
    def remove_background_from_url(self, image_url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Remove background from an image URL using rembg
        Returns: (success, base64_image, error_message)
        """
        try:
            if not self.is_configured():
                return False, None, "Background removal service not available. Please install rembg: pip install rembg"
            
            logger.info(f"Removing background from URL: {image_url}")
            
            # Download the image
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                return False, None, f"Failed to download image: {response.status_code}"
            
            # Process with rembg
            input_image = response.content
            output_image = remove(input_image, session=self.session)
            
            # Convert to base64
            base64_image = base64.b64encode(output_image).decode('utf-8')
            logger.info("Background removal successful")
            return True, base64_image, None
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout - please try again"
            logger.error(error_msg)
            return False, None, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def remove_background_from_file(self, file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Remove background from a local file using rembg
        Returns: (success, base64_image, error_message)
        """
        try:
            if not self.is_configured():
                return False, None, "Background removal service not available. Please install rembg: pip install rembg"
            
            logger.info(f"Removing background from file: {file_path}")
            
            # Read the file
            with open(file_path, 'rb') as image_file:
                input_image = image_file.read()
            
            # Process with rembg
            output_image = remove(input_image, session=self.session)
            
            # Convert to base64
            base64_image = base64.b64encode(output_image).decode('utf-8')
            logger.info("Background removal successful")
            return True, base64_image, None
                
        except FileNotFoundError:
            error_msg = "Image file not found"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def remove_background_from_base64(self, base64_image: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Remove background from a base64 encoded image using rembg
        Returns: (success, base64_image, error_message)
        """
        try:
            if not self.is_configured():
                return False, None, "Background removal service not available. Please install rembg: pip install rembg"
            
            logger.info("Removing background from base64 image")
            
            # Decode base64 image
            image_data = base64.b64decode(base64_image)
            
            # Process with rembg
            output_image = remove(image_data, session=self.session)
            
            # Convert back to base64
            result_base64 = base64.b64encode(output_image).decode('utf-8')
            logger.info("Background removal successful")
            return True, result_base64, None
                    
        except Exception as e:
            error_msg = f"Error processing base64 image: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def get_api_usage(self) -> Optional[dict]:
        """Get service status information"""
        try:
            if not self.is_configured():
                return {
                    "status": "not_available",
                    "message": "rembg library not installed or configured"
                }
            
            return {
                "status": "available",
                "message": "rembg background removal service is ready",
                "model": "u2net",
                "cost": "free"
            }
                
        except Exception as e:
            logger.error(f"Error getting service status: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

# Create singleton instance
background_removal_service = BackgroundRemovalService()
