"""
Replicate API Service for Virtual Try-On
Uses Replicate's API to generate realistic virtual try-on images
"""

import os
import base64
import logging
import requests
from typing import Optional, Dict
from PIL import Image
import io
import time
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()

logger = logging.getLogger(__name__)

# Try to import replicate, handle if not installed
try:
    import replicate
    REPLICATE_AVAILABLE = True
    logger.info("Replicate library loaded successfully")
except ImportError:
    REPLICATE_AVAILABLE = False
    logger.warning("Replicate library not installed. Install with: pip install replicate")


class ReplicateService:
    """Service for virtual try-on using Replicate API"""
    
    def __init__(self):
        # Try multiple ways to get the token
        self.api_token = os.getenv("REPLICATE_API_TOKEN")
        
        # If not found, try loading .env again
        if not self.api_token:
            load_dotenv()
            self.api_token = os.getenv("REPLICATE_API_TOKEN")
        
        self.model_version = os.getenv(
            "REPLICATE_TRYON_MODEL",
            "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4"
        )
        
        if not self.api_token:
            logger.warning("REPLICATE_API_TOKEN not set in environment variables")
            logger.warning(f"Current working directory: {os.getcwd()}")
            logger.warning(f".env file exists: {os.path.exists('.env')}")
        else:
            logger.info(f"✅ REPLICATE_API_TOKEN loaded successfully (length: {len(self.api_token)})")
    
    def is_available(self) -> bool:
        """Check if Replicate service is available"""
        # Re-check token in case it was set after initialization
        if not self.api_token:
            self.api_token = os.getenv("REPLICATE_API_TOKEN")
        return REPLICATE_AVAILABLE and self.api_token is not None
    
    async def create_virtual_tryon(
        self,
        person_image: Image.Image,
        garment_image: Image.Image,
        category: str = "upper_body",
        garment_description: Optional[str] = None,
        num_inference_steps: int = 30,
        guidance_scale: float = 2.0
    ) -> Optional[Dict]:
        """
        Create virtual try-on using Replicate API
        
        Args:
            person_image: PIL Image of the person
            garment_image: PIL Image of the garment
            category: Clothing category ("upper_body", "lower_body", "dresses")
            num_inference_steps: Number of denoising steps (default: 30)
            guidance_scale: Guidance scale for generation (default: 2.0)
            
        Returns:
            Dict with result image data or None if failed
        """
        try:
            # Re-check token in case it was set after service initialization
            if not self.api_token:
                self.api_token = os.getenv("REPLICATE_API_TOKEN")
                logger.info(f"🔍 Re-checked REPLICATE_API_TOKEN: {'Set' if self.api_token else 'Not set'}")
            
            # Also set it in replicate client if available
            if self.api_token and REPLICATE_AVAILABLE:
                import replicate as replicate_client
                replicate_client.Client(api_token=self.api_token)
                logger.info("✅ Replicate client configured with API token")
            
            if not self.is_available():
                logger.error(f"❌ Replicate service not available - REPLICATE_AVAILABLE: {REPLICATE_AVAILABLE}, api_token: {self.api_token is not None}")
                logger.error(f"❌ Token value: {self.api_token[:10] + '...' if self.api_token and len(self.api_token) > 10 else 'None'}")
                return None
            
            logger.info(f"🎨 Creating virtual try-on with Replicate for category: {category}")
            start_time = time.time()
            
            # Convert PIL images to base64 data URLs
            logger.info("🚀 Converting images to data URLs...")
            person_data_url = self._image_to_data_url(person_image)
            garment_data_url = self._image_to_data_url(garment_image)
            
            logger.info(f"🚀 Person data URL: {'Set' if person_data_url else 'None'}, length: {len(person_data_url) if person_data_url else 0}")
            logger.info(f"🚀 Garment data URL: {'Set' if garment_data_url else 'None'}, length: {len(garment_data_url) if garment_data_url else 0}")
            
            if not person_data_url or not garment_data_url:
                logger.error(f"❌ Failed to convert images to data URLs - person: {person_data_url is not None}, garment: {garment_data_url is not None}")
                return None
            
            # Map category to Replicate model's expected format
            category_mapping = {
                "tops": "upper_body",
                "shirts": "upper_body",
                "sweaters": "upper_body",
                "hoodies": "upper_body",
                "jackets": "upper_body",
                "outerwear": "upper_body",
                "bottoms": "lower_body",
                "pants": "lower_body",
                "jeans": "lower_body",
                "shorts": "lower_body",
                "dresses": "dresses",
            }
            
            replicate_category = category_mapping.get(category.lower(), "upper_body")
            
            # Generate garment description if not provided
            if not garment_description:
                garment_description = f"a {category.replace('_', ' ')}"
            
            # Run the model
            logger.info(f"🚀 Running Replicate model: {self.model_version}")
            logger.info(f"🚀 Input - person_data_url length: {len(person_data_url) if person_data_url else 0}")
            logger.info(f"🚀 Input - garment_data_url length: {len(garment_data_url) if garment_data_url else 0}")
            logger.info(f"🚀 Input - category: {replicate_category}")
            logger.info(f"🚀 Input - garment_des: {garment_description}")
            logger.info(f"🚀 Using API token: {self.api_token[:10] + '...' if self.api_token and len(self.api_token) > 10 else 'None'}")
            
            # Set the API token in the replicate client
            if self.api_token:
                os.environ["REPLICATE_API_TOKEN"] = self.api_token
                logger.info("✅ Set REPLICATE_API_TOKEN in environment")
            
            output = replicate.run(
                self.model_version,
                input={
                    "human_img": person_data_url,
                    "garm_img": garment_data_url,
                    "garment_des": garment_description,  # REQUIRED by the model
                    "category": replicate_category,
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                }
            )
            
            logger.info(f"🚀 Replicate output received: type={type(output)}")
            if output is None:
                logger.error("❌ Replicate output is None")
                return None
            
            # Handle generator/iterator output (Replicate FileOutput streams image chunks)
            if hasattr(output, '__iter__') and not isinstance(output, (str, list, dict, bytes)):
                logger.info("🚀 Replicate output is iterable (likely FileOutput stream), collecting all chunks...")
                try:
                    # Collect all chunks from the stream
                    chunks = []
                    total_bytes = 0
                    for chunk in output:
                        if isinstance(chunk, bytes):
                            chunks.append(chunk)
                            total_bytes += len(chunk)
                            logger.info(f"🚀 Collected chunk: {len(chunk)} bytes (total: {total_bytes} bytes)")
                        else:
                            logger.warning(f"⚠️ Non-bytes chunk received: {type(chunk)}")
                    
                    if chunks:
                        # Concatenate all chunks into complete image bytes
                        complete_image_bytes = b''.join(chunks)
                        logger.info(f"✅ Collected complete image: {len(complete_image_bytes)} bytes from {len(chunks)} chunks")
                        output = complete_image_bytes
                    else:
                        logger.error("❌ Iterator returned no chunks")
                        return None
                except Exception as e:
                    logger.error(f"❌ Error iterating Replicate output: {str(e)}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    return None
            
            try:
                if output:
                    if isinstance(output, (list, dict)):
                        length = len(output) if hasattr(output, '__len__') else None
                        length_str = str(length) if length is not None else '?'
                        output_str = f"{type(output).__name__} with {length_str} items"
                    else:
                        output_str = str(output) if output is not None else "None"
                    logger.info(f"🚀 Replicate output value: {output_str[:200] if output_str else 'None'}")
            except Exception as e:
                logger.warning(f"⚠️ Could not convert output to string: {e}")
                import traceback
                logger.warning(f"⚠️ Traceback: {traceback.format_exc()}")
            
            # Process the output
            if not output:
                logger.error("❌ No output received from Replicate")
                return None
            
            # Process the result image
            result_image = None
            
            try:
                # Check if output is already image bytes (starts with JPEG/PNG header)
                if isinstance(output, bytes):
                    logger.info(f"🚀 Replicate returned image bytes directly: {len(output)} bytes")
                    result_image = Image.open(io.BytesIO(output))
                elif isinstance(output, str):
                    # Check if it's a URL or base64 data
                    if output.startswith('http://') or output.startswith('https://'):
                        # It's a URL, download it
                        url_preview = output[:100] if len(output) > 100 else output
                        logger.info(f"🚀 Replicate returned URL: {url_preview}")
                        result_image = self._download_image(output)
                    elif output.startswith('data:image'):
                        # It's a data URL, extract base64
                        logger.info("🚀 Replicate returned data URL")
                        base64_data = output.split(',')[1] if ',' in output else output
                        image_bytes = base64.b64decode(base64_data)
                        result_image = Image.open(io.BytesIO(image_bytes))
                    else:
                        # Might be base64 string
                        try:
                            image_bytes = base64.b64decode(output)
                            result_image = Image.open(io.BytesIO(image_bytes))
                            logger.info("🚀 Replicate returned base64 string, decoded successfully")
                        except:
                            # Treat as URL anyway
                            logger.info(f"🚀 Replicate returned string (treating as URL): {output[:100]}")
                            result_image = self._download_image(output)
                elif isinstance(output, list) and len(output) > 0:
                    # List of outputs, take the first one
                    first_item = output[0]
                    logger.info(f"🚀 Replicate returned list with {len(output)} items, processing first item: type={type(first_item)}")
                    
                    if isinstance(first_item, bytes):
                        logger.info(f"🚀 First item is bytes: {len(first_item)} bytes")
                        result_image = Image.open(io.BytesIO(first_item))
                    elif isinstance(first_item, str):
                        if first_item.startswith('http://') or first_item.startswith('https://'):
                            result_image = self._download_image(first_item)
                        elif first_item.startswith('data:image'):
                            base64_data = first_item.split(',')[1] if ',' in first_item else first_item
                            image_bytes = base64.b64decode(base64_data)
                            result_image = Image.open(io.BytesIO(image_bytes))
                        else:
                            try:
                                image_bytes = base64.b64decode(first_item)
                                result_image = Image.open(io.BytesIO(image_bytes))
                            except:
                                result_image = self._download_image(first_item)
                    else:
                        logger.error(f"❌ Unexpected type in output list: {type(first_item)}")
                        return None
                else:
                    logger.error(f"❌ Unexpected output type from Replicate: {type(output)}")
                    logger.error(f"❌ Output value (first 200 chars): {str(output)[:200] if output else 'None'}")
                    return None
            except Exception as e:
                logger.error(f"❌ Error processing Replicate output: {str(e)}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                return None
            
            if not result_image:
                logger.error(f"❌ Failed to process result image from Replicate")
                return None
            
            logger.info(f"✅ Successfully processed result image: size={result_image.size}, mode={result_image.mode}")
            
            logger.info(f"✅ Successfully downloaded result image: size={result_image.size}, mode={result_image.mode}")
            
            # Convert result to base64
            result_base64 = self._image_to_base64(result_image)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Virtual try-on completed in {processing_time:.2f} seconds")
            
            return {
                "image_base64": result_base64,
                "confidence": 0.95,  # Replicate models are high quality
                "method": "replicate_idm_vton",
                "processing_time": processing_time,
                "category": replicate_category
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating virtual try-on with Replicate: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
            return None
    
    def _image_to_data_url(self, image: Image.Image) -> Optional[str]:
        """Convert PIL Image to data URL format"""
        try:
            if image is None:
                logger.error("❌ Cannot convert None image to data URL")
                return None
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            
            if not image_bytes:
                logger.error("❌ Image bytes are empty")
                return None
            
            # Encode to base64
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            
            if not base64_string:
                logger.error("❌ Base64 string is empty")
                return None
            
            # Create data URL
            data_url = f"data:image/png;base64,{base64_string}"
            
            return data_url
            
        except Exception as e:
            logger.error(f"❌ Error converting image to data URL: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            
            # Encode to base64
            base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return base64_string
            
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            return ""
    
    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                return image
            else:
                logger.error(f"Failed to download image: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None
    
    def get_service_status(self) -> Dict:
        """Get service status and configuration"""
        return {
            "available": self.is_available(),
            "api_token_set": self.api_token is not None,
            "model_version": self.model_version,
            "library_installed": REPLICATE_AVAILABLE
        }


# Global instance
replicate_service = ReplicateService()
