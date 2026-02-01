"""
Image cropping service for cloth images
"""
import base64
import io
import logging
from typing import Dict, Optional, Tuple

import numpy as np
import requests
from fastapi import HTTPException
from PIL import Image

logger = logging.getLogger(__name__)


class ImageCropService:
    """Service for cropping cloth images with auto-detection or manual coordinates"""
    
    def __init__(self):
        logger.info("ImageCropService initialized")
    
    def _detect_cloth_bounds(self, image: Image.Image) -> Tuple[int, int, int, int]:
        """
        Auto-detect cloth boundaries in an image
        Returns: (left, top, right, bottom) coordinates
        """
        try:
            # Convert image to RGB if needed
            if image.mode != 'RGB':
                if image.mode == 'RGBA':
                    # Create white background
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3] if len(image.split()) > 3 else None)
                    image = background
                else:
                    image = image.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Convert to grayscale for processing
            gray = np.mean(img_array, axis=2).astype(np.uint8)
            
            # Find non-white pixels (assuming white/light background)
            # Threshold to detect non-background pixels
            threshold = 240
            non_bg_mask = gray < threshold
            
            # Find bounding box
            rows = np.any(non_bg_mask, axis=1)
            cols = np.any(non_bg_mask, axis=0)
            
            if not rows.any() or not cols.any():
                # No object detected, return full image bounds
                logger.warning("No object detected, returning full image bounds")
                return 0, 0, image.width, image.height
            
            row_indices = np.where(rows)[0]
            col_indices = np.where(cols)[0]
            
            top = int(row_indices[0])
            bottom = int(row_indices[-1])
            left = int(col_indices[0])
            right = int(col_indices[-1])
            
            # Add padding (10% on each side)
            padding_x = int((right - left) * 0.05)
            padding_y = int((bottom - top) * 0.05)
            
            left = max(0, left - padding_x)
            top = max(0, top - padding_y)
            right = min(image.width, right + padding_x)
            bottom = min(image.height, bottom + padding_y)
            
            logger.info(f"Auto-detected bounds: left={left}, top={top}, right={right}, bottom={bottom}")
            return left, top, right, bottom
            
        except Exception as e:
            logger.error(f"Error detecting cloth bounds: {str(e)}")
            # Return full image bounds on error
            return 0, 0, image.width, image.height
    
    def _crop_image(
        self, 
        image: Image.Image, 
        left: Optional[int] = None,
        top: Optional[int] = None,
        right: Optional[int] = None,
        bottom: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        auto_detect: bool = True
    ) -> Image.Image:
        """
        Crop image with given coordinates or auto-detection
        
        Args:
            image: PIL Image to crop
            left: Left coordinate
            top: Top coordinate
            right: Right coordinate (mutually exclusive with width)
            bottom: Bottom coordinate (mutually exclusive with height)
            width: Width of crop (alternative to right)
            height: Height of crop (alternative to bottom)
            auto_detect: Auto-detect cloth boundaries if coordinates not provided
        """
        try:
            # If auto_detect and no coordinates provided, detect bounds
            if auto_detect and left is None and top is None:
                left, top, right, bottom = self._detect_cloth_bounds(image)
            else:
                # Use provided coordinates or defaults
                left = left if left is not None else 0
                top = top if top is not None else 0
                
                # Calculate right and bottom from width/height if provided
                if width is not None:
                    right = left + width
                elif right is None:
                    right = image.width
                
                if height is not None:
                    bottom = top + height
                elif bottom is None:
                    bottom = image.height
            
            # Validate coordinates
            left = max(0, min(left, image.width))
            top = max(0, min(top, image.height))
            right = max(left, min(right, image.width))
            bottom = max(top, min(bottom, image.height))
            
            # Crop the image
            cropped = image.crop((left, top, right, bottom))
            logger.info(f"Image cropped to: {left}, {top}, {right}, {bottom}")
            
            return cropped
            
        except Exception as e:
            logger.error(f"Error cropping image: {str(e)}")
            raise
    
    def _image_to_base64(self, image: Image.Image, format: str = 'PNG') -> str:
        """Convert PIL Image to base64 string"""
        buffered = io.BytesIO()
        image.save(buffered, format=format)
        img_bytes = buffered.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')
    
    def crop_from_url(
        self, 
        image_url: str,
        crop_params: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict]]:
        """
        Crop image from URL
        
        Args:
            image_url: URL of the image
            crop_params: Optional dict with crop parameters (left, top, right, bottom, width, height, auto_detect)
        
        Returns: (success, base64_image, error_message, crop_info)
        """
        try:
            logger.info(f"Cropping image from URL: {image_url}")
            
            # Download the image
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                return False, None, f"Failed to download image: {response.status_code}", None
            
            # Open image
            image = Image.open(io.BytesIO(response.content))
            original_size = image.size
            
            # Get crop parameters
            params = crop_params or {}
            left = params.get('left')
            top = params.get('top')
            right = params.get('right')
            bottom = params.get('bottom')
            width = params.get('width')
            height = params.get('height')
            auto_detect = params.get('auto_detect', True)
            
            # Crop the image
            cropped = self._crop_image(
                image, 
                left=left, 
                top=top, 
                right=right, 
                bottom=bottom,
                width=width,
                height=height,
                auto_detect=auto_detect
            )
            
            # Convert to base64
            base64_image = self._image_to_base64(cropped)
            
            crop_info = {
                'original_size': {'width': original_size[0], 'height': original_size[1]},
                'cropped_size': {'width': cropped.width, 'height': cropped.height}
            }
            
            logger.info("Image cropped successfully")
            return True, base64_image, None, crop_info
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout - please try again"
            logger.error(error_msg)
            return False, None, error_msg, None
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg, None
    
    def crop_from_base64(
        self,
        base64_image: str,
        crop_params: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict]]:
        """
        Crop image from base64 encoded string
        
        Args:
            base64_image: Base64 encoded image
            crop_params: Optional dict with crop parameters (left, top, right, bottom, width, height, auto_detect)
        
        Returns: (success, base64_image, error_message, crop_info)
        """
        try:
            logger.info("Cropping base64 image")
            
            # Decode base64 image
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
            original_size = image.size
            
            # Get crop parameters
            params = crop_params or {}
            left = params.get('left')
            top = params.get('top')
            right = params.get('right')
            bottom = params.get('bottom')
            width = params.get('width')
            height = params.get('height')
            auto_detect = params.get('auto_detect', True)
            
            # Crop the image
            cropped = self._crop_image(
                image,
                left=left,
                top=top,
                right=right,
                bottom=bottom,
                width=width,
                height=height,
                auto_detect=auto_detect
            )
            
            # Convert back to base64
            result_base64 = self._image_to_base64(cropped)
            
            crop_info = {
                'original_size': {'width': original_size[0], 'height': original_size[1]},
                'cropped_size': {'width': cropped.width, 'height': cropped.height}
            }
            
            logger.info("Image cropped successfully")
            return True, result_base64, None, crop_info
                    
        except Exception as e:
            error_msg = f"Error processing base64 image: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg, None


# Create singleton instance
image_crop_service = ImageCropService()

