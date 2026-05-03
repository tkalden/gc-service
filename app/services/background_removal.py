"""
Background removal service using rembg (free local processing)
"""
import base64
import io
import logging
import os
import tempfile
from typing import Optional, Tuple

import requests
from fastapi import HTTPException
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import rembg, handle if not installed or native deps fail
try:
    from rembg import new_session, remove

    REMBG_AVAILABLE = True
    logger.info("rembg library loaded successfully")
except (ImportError, OSError) as e:
    REMBG_AVAILABLE = False
    logger.warning(
        "rembg unavailable: %s. Try: pip install 'rembg[cpu]' "
        "(installs onnxruntime on Linux).",
        e,
    )

class BackgroundRemovalService:
    def __init__(self):
        self.session = None
        self.better_session = None
        if REMBG_AVAILABLE:
            try:
                # Try different initialization methods for rembg compatibility
                try:
                    # Try with u2net_human_seg model first (better for clothing)
                    self.better_session = new_session('u2net_human_seg')
                    logger.info("rembg session initialized with u2net_human_seg model (better for clothing)")
                except Exception as e1:
                    logger.warning(f"u2net_human_seg model failed: {e1}, trying u2net")
                    try:
                        # Try with u2net model
                        self.session = new_session('u2net')
                        logger.info("rembg session initialized with u2net model")
                    except Exception as e2:
                        logger.warning(f"u2net model failed: {e2}, trying default model")
                        try:
                            # Try with default model
                            self.session = new_session()
                            logger.info("rembg session initialized with default model")
                        except Exception as e3:
                            logger.warning(f"Default model failed: {e3}, trying without session")
                            # Try without session (direct remove function)
                            self.session = "direct"  # Use direct remove function
                            logger.info("Using direct rembg remove function")
            except Exception as e:
                logger.error(f"Failed to initialize rembg: {e}")
                self.session = None
    
    def is_configured(self) -> bool:
        """Check if the background removal service is available"""
        return REMBG_AVAILABLE and (self.session is not None or self.better_session is not None)
    
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
    
    def remove_background_from_base64(self, base64_image: str, auto_crop: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Remove background from a base64 encoded image using rembg
        Optionally auto-crop to clothing boundaries
        Returns: (success, base64_image, error_message)
        """
        try:
            if not self.is_configured():
                return False, None, "Background removal service not available. Please install rembg: pip install rembg"
            
            logger.info(f"Removing background from base64 image (auto_crop={auto_crop})")
            logger.info(f"Base64 image length: {len(base64_image)}")
            logger.info(f"Base64 image preview: {base64_image[:50]}...")
            
            # Decode base64 image
            image_data = base64.b64decode(base64_image)
            logger.info(f"Decoded image data length: {len(image_data)}")
            
            # Validate image data
            try:
                import io

                from PIL import Image

                # Try to open the image to validate it
                image = Image.open(io.BytesIO(image_data))
                logger.info(f"Image validated: {image.size}, format: {image.format}")
            except Exception as e:
                logger.error(f"Invalid image data: {str(e)}")
                return False, None, f"Invalid image data: {str(e)}"
            
            # Process with rembg using the best available model
            if self.better_session is not None:
                # Use the better human segmentation model
                output_image = remove(image_data, session=self.better_session)
                logger.info("Used u2net_human_seg model for better clothing segmentation")
            elif self.session == "direct":
                # Use direct remove function without session
                output_image = remove(image_data)
            else:
                # Use session-based remove function
                output_image = remove(image_data, session=self.session)
            
            # Post-process to clean up remaining background and remove hangers
            output_image = self._clean_background(output_image)
            output_image = self._remove_hangers_and_objects(output_image)
            
            # If auto_crop is enabled, crop to clothing boundaries
            if auto_crop:
                output_image = self._crop_to_content(output_image)
            
            # Convert back to base64
            result_base64 = base64.b64encode(output_image).decode('utf-8')
            logger.info("Background removal successful")
            return True, result_base64, None
                    
        except Exception as e:
            error_msg = f"Error processing base64 image: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _clean_background(self, image_data: bytes) -> bytes:
        """
        Clean up remaining background by analyzing alpha channel
        Makes semi-transparent areas either fully transparent or fully opaque
        """
        try:
            import io

            import numpy as np
            from PIL import Image

            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Get alpha channel
            alpha = img_array[:, :, 3]
            
            # Apply threshold: pixels with low alpha become fully transparent
            # This removes leftover semi-transparent background
            threshold = 30  # Lower threshold for better background removal
            alpha[alpha < threshold] = 0
            
            # Additional cleanup: remove pixels that are mostly transparent
            # This helps remove hangers and other objects that might have low opacity
            alpha[alpha < 100] = 0
            
            # Update alpha channel
            img_array[:, :, 3] = alpha
            
            # Convert back to image
            cleaned_img = Image.fromarray(img_array, 'RGBA')
            
            # Convert back to bytes
            output = io.BytesIO()
            cleaned_img.save(output, format='PNG')
            cleaned_bytes = output.getvalue()
            
            logger.info("Background cleaned successfully")
            return cleaned_bytes
            
        except Exception as e:
            logger.error(f"Error cleaning background: {str(e)}")
            # Return original on error
            return image_data
    
    def _remove_hangers_and_objects(self, image_data: bytes) -> bytes:
        """
        Remove hangers and other non-clothing objects using edge detection and shape analysis
        """
        try:
            import io

            import numpy as np
            from PIL import Image
            from scipy import ndimage
            from skimage import filters, measure, morphology

            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Get alpha channel
            alpha = img_array[:, :, 3]
            
            # Create binary mask of non-transparent pixels
            binary_mask = alpha > 0
            
            # Find connected components
            labeled_array, num_features = measure.label(binary_mask, return_num=True)
            
            if num_features == 0:
                return image_data
            
            # Analyze each connected component
            for region in measure.regionprops(labeled_array):
                # Get the region coordinates
                minr, minc, maxr, maxc = region.bbox
                region_mask = labeled_array[minr:maxr, minc:maxc] == region.label
                
                # Calculate region properties
                area = region.area
                bbox_area = (maxr - minr) * (maxc - minc)
                solidity = area / bbox_area if bbox_area > 0 else 0
                
                # Get the region's aspect ratio
                height = maxr - minr
                width = maxc - minc
                aspect_ratio = height / width if width > 0 else 0
                
                # Detect hangers and thin objects
                is_hanger = (
                    # Thin vertical objects (hangers)
                    (aspect_ratio > 3 and width < 20) or
                    # Thin horizontal objects (hanger bars)
                    (aspect_ratio < 0.3 and height < 20) or
                    # Very small objects (likely hanger hooks)
                    (area < 100) or
                    # Low solidity (irregular shapes like hangers)
                    (solidity < 0.3 and area < 500)
                )
                
                # Detect other non-clothing objects
                is_non_clothing = (
                    # Very small isolated objects
                    (area < 50) or
                    # Objects that are too thin (strings, wires)
                    (min(height, width) < 5) or
                    # Objects with very low solidity (likely background artifacts)
                    (solidity < 0.2 and area < 200)
                )
                
                # Remove detected hangers and non-clothing objects
                if is_hanger or is_non_clothing:
                    logger.info(f"Removing object: area={area}, aspect_ratio={aspect_ratio:.2f}, solidity={solidity:.2f}")
                    # Set alpha to 0 for this region
                    alpha[minr:maxr, minc:maxc][region_mask] = 0
            
            # Update alpha channel
            img_array[:, :, 3] = alpha
            
            # Additional cleanup: remove isolated pixels
            alpha_cleaned = morphology.remove_small_objects(alpha > 0, min_size=10)
            img_array[:, :, 3] = alpha_cleaned.astype(np.uint8) * 255
            
            # Convert back to image
            cleaned_img = Image.fromarray(img_array, 'RGBA')
            
            # Convert back to bytes
            output = io.BytesIO()
            cleaned_img.save(output, format='PNG')
            cleaned_bytes = output.getvalue()
            
            logger.info("Hangers and non-clothing objects removed successfully")
            return cleaned_bytes
            
        except ImportError as e:
            logger.warning(f"scikit-image not available for advanced processing: {e}")
            # Fallback to basic cleanup
            return self._basic_cleanup(image_data)
        except Exception as e:
            logger.error(f"Error removing hangers and objects: {str(e)}")
            # Return original on error
            return image_data
    
    def _basic_cleanup(self, image_data: bytes) -> bytes:
        """
        Basic cleanup without advanced image processing libraries
        """
        try:
            import io

            import numpy as np
            from PIL import Image

            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Get alpha channel
            alpha = img_array[:, :, 3]
            
            # Remove very small isolated pixels (likely noise)
            # This is a simple approach without scikit-image
            alpha_cleaned = alpha.copy()
            
            # Simple noise removal: if a pixel is isolated (surrounded by transparent pixels), make it transparent
            for i in range(1, alpha.shape[0] - 1):
                for j in range(1, alpha.shape[1] - 1):
                    if alpha[i, j] > 0:  # If pixel is not transparent
                        # Check if it's isolated (surrounded by transparent pixels)
                        neighbors = alpha[i-1:i+2, j-1:j+2]
                        if np.sum(neighbors > 0) <= 1:  # Only itself is non-transparent
                            alpha_cleaned[i, j] = 0
            
            # Update alpha channel
            img_array[:, :, 3] = alpha_cleaned
            
            # Convert back to image
            cleaned_img = Image.fromarray(img_array, 'RGBA')
            
            # Convert back to bytes
            output = io.BytesIO()
            cleaned_img.save(output, format='PNG')
            cleaned_bytes = output.getvalue()
            
            logger.info("Basic cleanup completed")
            return cleaned_bytes
            
        except Exception as e:
            logger.error(f"Error in basic cleanup: {str(e)}")
            return image_data
    
    def _crop_to_content(self, image_data: bytes) -> bytes:
        """
        Crop image to the bounding box of non-transparent content
        """
        try:
            import io

            import numpy as np
            from PIL import Image

            # Open image
            img = Image.open(io.BytesIO(image_data))
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Get alpha channel
            alpha = img_array[:, :, 3]
            
            # Find bounding box of non-transparent pixels
            rows = np.any(alpha > 0, axis=1)
            cols = np.any(alpha > 0, axis=0)
            
            if not rows.any() or not cols.any():
                # No content found, return original
                logger.warning("No non-transparent content found, skipping crop")
                return image_data
            
            row_indices = np.where(rows)[0]
            col_indices = np.where(cols)[0]
            
            top = int(row_indices[0])
            bottom = int(row_indices[-1])
            left = int(col_indices[0])
            right = int(col_indices[-1])
            
            # Add small padding (5% of dimensions)
            padding_x = max(5, int((right - left) * 0.05))
            padding_y = max(5, int((bottom - top) * 0.05))
            
            left = max(0, left - padding_x)
            top = max(0, top - padding_y)
            right = min(img.width, right + padding_x)
            bottom = min(img.height, bottom + padding_y)
            
            # Crop image
            cropped_img = img.crop((left, top, right, bottom))
            
            # Convert back to bytes
            output = io.BytesIO()
            cropped_img.save(output, format='PNG')
            cropped_bytes = output.getvalue()
            
            logger.info(f"Cropped image from {img.size} to {cropped_img.size}")
            return cropped_bytes
            
        except Exception as e:
            logger.error(f"Error cropping to content: {str(e)}")
            # Return original on error
            return image_data
    
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
