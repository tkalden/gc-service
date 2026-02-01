"""
Avatar Service for Digital Twin Creation
Uses MediaPipe for pose detection and body segmentation
"""

import os
import uuid
import numpy as np
import base64
from typing import Optional, Tuple, Dict, List
from fastapi import HTTPException
import logging
from PIL import Image
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

# Import Replicate service for virtual try-on
from app.services.replicate_service import replicate_service


logger = logging.getLogger(__name__)

# Try to import OpenCV, handle if not installed
try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info("OpenCV library loaded successfully")
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV library not installed. Install with: pip install opencv-python")

# Try to import MediaPipe, handle if not installed
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    logger.info("MediaPipe library loaded successfully")
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("MediaPipe library not installed. Install with: pip install mediapipe")


class AvatarService:
    """Service for creating and managing digital twin avatars"""
    
    def __init__(self):
        self.pose_detector = None
        self.selfie_segmentation = None
        self.executor = ThreadPoolExecutor(max_workers=4)  # For CPU-intensive tasks
        
        if MEDIAPIPE_AVAILABLE:
            try:
                # Initialize MediaPipe Pose with simpler configuration
                mp_pose = mp.solutions.pose
                self.pose_detector = mp_pose.Pose(
                    static_image_mode=True,
                    model_complexity=1,  # Reduced from 2 to 1 for better compatibility
                    enable_segmentation=False,  # Disable segmentation initially to avoid config issues
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                
                # Initialize MediaPipe Selfie Segmentation
                mp_selfie_segmentation = mp.solutions.selfie_segmentation
                self.selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation(
                    model_selection=0  # Use model 0 (general) instead of 1 for better compatibility
                )
                
                logger.info("MediaPipe models initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MediaPipe models: {e}")
                logger.error(f"MediaPipe error details: {str(e)}")
                # Try with minimal configuration
                try:
                    logger.info("Attempting MediaPipe initialization with minimal config...")
                    self.pose_detector = mp_pose.Pose(
                        static_image_mode=True,
                        model_complexity=0,  # Simplest model
                        min_detection_confidence=0.5
                    )
                    self.selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation(
                        model_selection=0
                    )
                    logger.info("MediaPipe initialized with minimal config")
                except Exception as e2:
                    logger.error(f"MediaPipe initialization failed even with minimal config: {e2}")
                    self.pose_detector = None
                    self.selfie_segmentation = None
    
    def is_available(self) -> bool:
        """Check if the avatar service is available"""
        return OPENCV_AVAILABLE and MEDIAPIPE_AVAILABLE and self.pose_detector is not None
    
    async def process_avatar_image(self, image_data: bytes, user_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Process avatar image to extract pose and body segments
        Returns: (success, avatar_data, error_message)
        """
        try:
            if not self.is_available():
                return False, None, "Avatar service not available. Please install MediaPipe: pip install mediapipe"
            
            start_time = time.time()
            logger.info(f"Processing avatar for user: {user_id}")
            
            # Run CPU-intensive processing in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._process_image_sync, 
                image_data
            )
            
            success, pose_data, segmentation_data, processed_image, error = result
            
            if not success:
                return False, None, error
            
            processing_time = time.time() - start_time
            logger.info(f"Avatar processing completed in {processing_time:.2f} seconds")
            
            # Create avatar data structure
            avatar_data = {
                "pose_keypoints": pose_data,
                "body_segments": segmentation_data,
                "confidence_score": pose_data.get("confidence", 0.0) if pose_data else 0.0,
                "processing_time": processing_time,
                "processed_image_base64": processed_image
            }
            
            return True, avatar_data, None
            
        except Exception as e:
            logger.error(f"Error processing avatar image: {str(e)}")
            return False, None, f"Avatar processing failed: {str(e)}"
    
    def _process_image_sync(self, image_data: bytes) -> Tuple[bool, Optional[Dict], Optional[Dict], Optional[str], Optional[str]]:
        """
        Synchronous image processing (runs in thread pool)
        Returns: (success, pose_data, segmentation_data, processed_image_base64, error)
        """
        try:
            logger.info(f"Processing image data of size: {len(image_data)} bytes")
            
            if len(image_data) == 0:
                return False, None, None, None, "Empty image data received"
            
            if not OPENCV_AVAILABLE:
                return False, None, None, None, "OpenCV not available - cannot process image"
                
            # Convert bytes to OpenCV image
            nparr = np.frombuffer(image_data, np.uint8)
            logger.info(f"Created numpy array of shape: {nparr.shape}")
            
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return False, None, None, None, "Invalid image data - cv2.imdecode failed"
                
            logger.info(f"Successfully decoded image with shape: {image.shape}")
            
            # Convert BGR to RGB for MediaPipe
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process pose detection
            pose_results = self.pose_detector.process(rgb_image)
            pose_data = self._extract_pose_data(pose_results, rgb_image.shape)
            
            # Process body segmentation
            segmentation_results = self.selfie_segmentation.process(rgb_image)
            segmentation_data = self._extract_segmentation_data(segmentation_results, rgb_image.shape)
            
            # Create processed image with pose overlay
            processed_image = self._create_processed_image(rgb_image, pose_results)
            processed_image_base64 = self._image_to_base64(processed_image)
            
            return True, pose_data, segmentation_data, processed_image_base64, None
            
        except Exception as e:
            logger.error(f"Error in sync image processing: {str(e)}")
            return False, None, None, None, str(e)
    
    def _extract_pose_data(self, pose_results, image_shape) -> Optional[Dict]:
        """Extract pose keypoints and metadata"""
        if not pose_results.pose_landmarks:
            return None
        
        height, width = image_shape[:2]
        keypoints = []
        
        # Extract 33 pose landmarks
        for i, landmark in enumerate(pose_results.pose_landmarks.landmark):
            keypoint = {
                "id": i,
                "x": landmark.x * width,
                "y": landmark.y * height,
                "z": landmark.z,
                "visibility": landmark.visibility
            }
            keypoints.append(keypoint)
        
        # Calculate confidence score based on visibility
        visibility_scores = [kp["visibility"] for kp in keypoints]
        confidence = sum(visibility_scores) / len(visibility_scores)
        
        # Identify key body parts
        key_points = {
            "nose": keypoints[0] if len(keypoints) > 0 else None,
            "left_shoulder": keypoints[11] if len(keypoints) > 11 else None,
            "right_shoulder": keypoints[12] if len(keypoints) > 12 else None,
            "left_hip": keypoints[23] if len(keypoints) > 23 else None,
            "right_hip": keypoints[24] if len(keypoints) > 24 else None,
        }
        
        return {
            "keypoints": keypoints,
            "key_points": key_points,
            "confidence": confidence,
            "total_landmarks": len(keypoints)
        }
    
    def _extract_segmentation_data(self, segmentation_results, image_shape) -> Optional[Dict]:
        """Extract body segmentation data"""
        if segmentation_results.segmentation_mask is None:
            return None
        
        height, width = image_shape[:2]
        
        # Convert segmentation mask to binary mask
        mask = segmentation_results.segmentation_mask
        binary_mask = (mask > 0.5).astype(np.uint8)
        
        # Calculate segmentation statistics
        total_pixels = height * width
        body_pixels = np.sum(binary_mask)
        body_ratio = body_pixels / total_pixels
        
        # Find bounding box of the person
        coords = np.where(binary_mask > 0)
        if len(coords[0]) > 0:
            y_min, y_max = np.min(coords[0]), np.max(coords[0])
            x_min, x_max = np.min(coords[1]), np.max(coords[1])
            
            bounding_box = {
                "x_min": int(x_min),
                "y_min": int(y_min),
                "x_max": int(x_max),
                "y_max": int(y_max),
                "width": int(x_max - x_min),
                "height": int(y_max - y_min)
            }
        else:
            bounding_box = None
        
        return {
            "body_ratio": float(body_ratio),
            "body_pixels": int(body_pixels),
            "total_pixels": total_pixels,
            "bounding_box": bounding_box,
            "mask_shape": mask.shape
        }
    
    def _create_processed_image(self, rgb_image: np.ndarray, pose_results) -> np.ndarray:
        """Create processed image with pose overlay"""
        try:
            # Create a copy of the original image
            processed = rgb_image.copy()
            
            if pose_results.pose_landmarks:
                # Draw pose landmarks
                mp_drawing = mp.solutions.drawing_utils
                mp_pose = mp.solutions.pose
                
                mp_drawing.draw_landmarks(
                    processed,
                    pose_results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing.DrawingSpec(
                        color=(0, 255, 0), thickness=2, circle_radius=2
                    ),
                    connection_drawing_spec=mp_drawing.DrawingSpec(
                        color=(255, 0, 0), thickness=2
                    )
                )
            
            return processed
            
        except Exception as e:
            logger.error(f"Error creating processed image: {str(e)}")
            return rgb_image  # Return original if processing fails
    
    def _image_to_base64(self, image: np.ndarray) -> str:
        """Convert numpy image to base64 string"""
        try:
            # Convert RGB to PIL Image
            pil_image = Image.fromarray(image)
            
            # Convert to bytes
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            
            # Encode to base64
            base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return base64_string
            
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            return ""
    
    async def validate_avatar_quality(self, avatar_data: Dict) -> Tuple[bool, str, float]:
        """
        Validate avatar quality for virtual try-on
        Returns: (is_valid, message, quality_score)
        """
        try:
            pose_data = avatar_data.get("pose_keypoints")
            segmentation_data = avatar_data.get("body_segments")
            
            if not pose_data or not segmentation_data:
                return False, "Missing pose or segmentation data", 0.0
            
            confidence = pose_data.get("confidence", 0.0)
            body_ratio = segmentation_data.get("body_ratio", 0.0)
            
            # Quality checks
            if confidence < 0.5:
                return False, "Pose detection confidence too low. Please use a clearer image.", confidence
            
            if body_ratio < 0.1:
                return False, "Person not clearly visible in image. Please use a full-body photo.", body_ratio
            
            # Calculate overall quality score
            quality_score = (confidence * 0.7) + (min(body_ratio * 2, 1.0) * 0.3)
            
            if quality_score < 0.6:
                return False, f"Image quality too low for virtual try-on (score: {quality_score:.2f})", quality_score
            
            return True, "Avatar ready for virtual try-on", quality_score
            
        except Exception as e:
            logger.error(f"Error validating avatar quality: {str(e)}")
            return False, "Error validating avatar quality", 0.0

    async def perform_virtual_try_on(self, request, user_id: str) -> Dict:
        """
        Perform virtual try-on
        """
        try:
            logger.info(f"🎯 [AvatarService] perform_virtual_try_on called: avatar_id={request.avatar_id}, clothing_id={request.clothing_item_id}, user_id={user_id}")
            
            from app.services.database_service import DatabaseService
            
            # 1. Get Avatar
            logger.info(f"🎯 [AvatarService] Fetching avatar: {request.avatar_id}")
            avatar = await DatabaseService.get_avatar_by_id(request.avatar_id)
            if not avatar:
                logger.error(f"❌ [AvatarService] Avatar not found: {request.avatar_id}")
                raise HTTPException(status_code=404, detail="Avatar not found")
            
            logger.info(f"✅ [AvatarService] Avatar found: id={avatar.id}, image_path={avatar.original_image_path}")
            
            if avatar.user_id != user_id:
                logger.error(f"❌ [AvatarService] Access denied: avatar.user_id={avatar.user_id} != user_id={user_id}")
                raise HTTPException(status_code=403, detail="Access denied to avatar")
                
            # 2. Get Clothing Item
            logger.info(f"🎯 [AvatarService] Fetching clothing item: {request.clothing_item_id}")
            clothing_item = await DatabaseService.get_clothing_item_by_id(request.clothing_item_id)
            if not clothing_item:
                logger.error(f"❌ [AvatarService] Clothing item not found: {request.clothing_item_id}")
                raise HTTPException(status_code=404, detail="Clothing item not found")
            
            logger.info(f"✅ [AvatarService] Clothing item found: id={clothing_item.id}, name={clothing_item.name}, category={clothing_item.category}, image_path={clothing_item.image_path}")
                
            # 3. Generate Preview
            logger.info(f"🎯 [AvatarService] Generating try-on preview...")
            # Use generate_try_on_preview which handles the logic
            preview_result = await self.generate_try_on_preview(
                avatar_path=avatar.original_image_path,
                clothing_path=clothing_item.image_path,
                clothing_name=clothing_item.name,
                clothing_category=clothing_item.category,
                pose_keypoints=avatar.pose_keypoints
            )
            
            if not preview_result:
                raise Exception("Failed to generate try-on preview")
                
            # Map keys to match frontend expectations
            if "image_base64" in preview_result:
                preview_result["preview_image"] = preview_result["image_base64"]
                logger.info(f"✅ Mapped image_base64 to preview_image, length: {len(preview_result['preview_image'])}")
            else:
                logger.warning(f"⚠️ No image_base64 in preview_result. Keys: {preview_result.keys() if preview_result else 'None'}")
                
            logger.info(f"✅ Returning preview_result with keys: {list(preview_result.keys()) if preview_result else 'None'}")
            return preview_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in perform_virtual_try_on: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def generate_try_on_preview(
        self, 
        avatar_path: str, 
        clothing_path: str, 
        clothing_name: str, 
        clothing_category: str,
        pose_keypoints: Optional[dict] = None
    ) -> Optional[Dict]:
        """
        Generate a temporary try-on preview without storing files
        Returns base64 image data for immediate display
        """
        try:
            logger.info(f"🎯 [AvatarService] generate_try_on_preview called: clothing={clothing_name}, category={clothing_category}")
            logger.info(f"🎯 [AvatarService] avatar_path={avatar_path}, clothing_path={clothing_path}")
            
            # For now, create a simple composite preview
            # In a real implementation, this would use advanced AI for clothing overlay
            
            # Download avatar image from storage using service key (more reliable than public URL)
            from app.services.storage_service import StorageService
            logger.info(f"🎯 [AvatarService] Downloading avatar image content directly from storage...")
            avatar_content, avatar_content_type = await StorageService.download_image_content(avatar_path)
            
            if not avatar_content:
                logger.error(f"❌ [AvatarService] Failed to download avatar image content")
                raise Exception(f"Failed to download avatar image from storage")
            
            logger.info(f"✅ [AvatarService] Avatar image downloaded: {len(avatar_content)} bytes, type: {avatar_content_type}")
            
            # Create avatar image from bytes
            avatar_image = Image.open(io.BytesIO(avatar_content))
            if avatar_image.mode != 'RGB':
                avatar_image = avatar_image.convert('RGB')
            logger.info(f"✅ [AvatarService] Avatar image loaded: size={avatar_image.size}, mode={avatar_image.mode}")
            
            # Download clothing image
            logger.info(f"🎯 [AvatarService] Downloading clothing image content directly from storage...")
            clothing_content, clothing_content_type = await StorageService.download_image_content(clothing_path)
            
            clothing_image = None
            if clothing_content:
                clothing_image = Image.open(io.BytesIO(clothing_content))
                if clothing_image.mode not in ['RGB', 'RGBA']:
                    clothing_image = clothing_image.convert('RGB')
                logger.info(f"✅ [AvatarService] Clothing image loaded: size={clothing_image.size}, mode={clothing_image.mode}")
            else:
                logger.warning(f"⚠️ [AvatarService] Failed to download clothing image content")
            
            # Create actual virtual try-on using Replicate API (required, no fallback)
            logger.info(f"🎯 [AvatarService] Calling _create_virtual_tryon_direct with images...")
            preview_result = await self._create_virtual_tryon_direct(
                avatar_image, clothing_image, clothing_name, clothing_category, pose_keypoints
            )
            
            logger.info(f"🎯 [AvatarService] _create_virtual_tryon_direct returned: method={preview_result.get('method')}, confidence={preview_result.get('confidence')}")
            logger.info(f"🎯 [AvatarService] Image data length: {len(preview_result.get('image_base64', ''))}")
            
            # Return the result directly (already has image_base64, confidence, method)
            return preview_result
            
        except Exception as e:
            logger.error(f"Error generating try-on preview: {str(e)}")
            return None
    
    async def _create_virtual_tryon_direct(self, avatar_image: Image.Image, clothing_image: Optional[Image.Image], clothing_name: str, category: str, pose_keypoints: dict) -> Dict:
        """Create virtual try-on using already-loaded images - PRIORITIZES REPLICATE"""
        try:
            logger.info(f"🎯 [AvatarService] _create_virtual_tryon_direct called: avatar_size={avatar_image.size}, has_clothing={clothing_image is not None}, category={category}")
            
            # PRIORITY 1: Try to use Replicate API for high-quality virtual try-on
            logger.info(f"🔍 Checking Replicate availability: is_available={replicate_service.is_available()}, has_clothing_image={clothing_image is not None}")
            
            if not replicate_service.is_available():
                logger.error("❌ Replicate service not available - CANNOT use Replicate")
                logger.error(f"❌ Replicate available check: {replicate_service.is_available()}")
                logger.error(f"❌ Replicate API token: {'Set' if replicate_service.api_token else 'Not set'}")
                raise Exception("Replicate service not available. Please configure REPLICATE_API_TOKEN in .env file")
            
            if not clothing_image:
                logger.error("❌ No clothing image provided - CANNOT use Replicate")
                raise Exception("Clothing image is required for virtual try-on")
            
            # Replicate is available and we have clothing image - USE IT
            logger.info("🚀🚀🚀 USING REPLICATE API FOR VIRTUAL TRY-ON 🚀🚀🚀")
            logger.info(f"🚀 Avatar image size: {avatar_image.size}, mode: {avatar_image.mode}")
            logger.info(f"🚀 Clothing image size: {clothing_image.size}, mode: {clothing_image.mode}")
            logger.info(f"🚀 Category: {category}")
            
            try:
                replicate_result = await replicate_service.create_virtual_tryon(
                    person_image=avatar_image,
                    garment_image=clothing_image,
                    category=category
                )
                
                logger.info(f"🚀 Replicate result received: {type(replicate_result)}, has image_base64: {bool(replicate_result and replicate_result.get('image_base64'))}")
                
                if replicate_result and replicate_result.get("image_base64"):
                    image_base64_len = len(replicate_result["image_base64"])
                    logger.info(f"✅✅✅ REPLICATE VIRTUAL TRY-ON SUCCESSFUL! Image base64 length: {image_base64_len} ✅✅✅")
                    
                    # Return the full result dict with method info
                    return {
                        "image_base64": replicate_result["image_base64"],
                        "confidence": replicate_result.get("confidence", 0.95),
                        "method": replicate_result.get("method", "replicate_idm_vton"),
                        "processing_time": replicate_result.get("processing_time", 0)
                    }
                else:
                    logger.error("❌ Replicate returned no result")
                    logger.error(f"❌ Replicate result: {replicate_result}")
                    raise Exception("Replicate API returned no image data")
                    
            except Exception as replicate_error:
                logger.error(f"❌❌❌ REPLICATE API ERROR - NOT FALLING BACK TO BASIC OVERLAY ❌❌❌")
                logger.error(f"❌ Error: {str(replicate_error)}")
                logger.error(f"❌ Error type: {type(replicate_error).__name__}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                raise Exception(f"Replicate API failed: {str(replicate_error)}")
            
        except Exception as e:
            logger.error(f"❌ Error in _create_virtual_tryon_direct: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise
            
        except Exception as e:
            logger.error(f"Error creating visual preview: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return original avatar as fallback
            try:
                buffer = io.BytesIO()
                avatar_image.save(buffer, format='PNG')
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
            except Exception as fallback_error:
                logger.error(f"Fallback avatar conversion also failed: {str(fallback_error)}")
                raise
    
    async def _create_virtual_tryon(self, avatar_url: str, clothing_path: str, clothing_name: str, category: str, pose_keypoints: dict) -> str:
        """Create actual virtual try-on by overlaying clothing on the avatar using Replicate API"""
        try:
            logger.info(f"🎯 [AvatarService] _create_virtual_tryon called: avatar_url={avatar_url}, clothing_path={clothing_path}, category={category}")
            
            import requests
            from PIL import Image, ImageDraw, ImageFont
            import io
            from app.services.storage_service import StorageService
            
            # Download avatar image
            logger.info(f"🎯 [AvatarService] Downloading avatar image from: {avatar_url}")
            logger.info(f"🎯 [AvatarService] Avatar URL length: {len(avatar_url) if avatar_url else 0}")
            
            try:
                response = requests.get(avatar_url, timeout=30)
                logger.info(f"🎯 [AvatarService] Avatar download response: status={response.status_code}, content_length={len(response.content) if response.content else 0}")
                
                if response.status_code != 200:
                    logger.error(f"❌ [AvatarService] Failed to download avatar: HTTP {response.status_code}")
                    logger.error(f"❌ [AvatarService] Response text: {response.text[:200] if response.text else 'No response text'}")
                    logger.error(f"❌ [AvatarService] Response headers: {dict(response.headers)}")
                    raise Exception(f"Failed to download avatar image: HTTP {response.status_code} from {avatar_url}")
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ [AvatarService] Request exception downloading avatar: {str(e)}")
                raise Exception(f"Failed to download avatar image: {str(e)}")
            
            # Open avatar image
            avatar_image = Image.open(io.BytesIO(response.content))
            if avatar_image.mode != 'RGB':
                avatar_image = avatar_image.convert('RGB')
            logger.info(f"✅ [AvatarService] Avatar image loaded: size={avatar_image.size}, mode={avatar_image.mode}")
            
            # Download clothing
            clothing_url = StorageService.get_image_url(clothing_path) if clothing_path else None
            logger.info(f"🎯 [AvatarService] Clothing URL: {clothing_url}")
            clothing_image = None
            
            if clothing_url:
                try:
                    logger.info(f"🎯 [AvatarService] Downloading clothing image from: {clothing_url}")
                    clothing_response = requests.get(clothing_url)
                    if clothing_response.status_code == 200:
                        clothing_image = Image.open(io.BytesIO(clothing_response.content))
                        if clothing_image.mode not in ['RGB', 'RGBA']:
                            clothing_image = clothing_image.convert('RGB')
                        logger.info(f"✅ [AvatarService] Clothing image loaded: size={clothing_image.size}, mode={clothing_image.mode}")
                    else:
                        logger.error(f"❌ [AvatarService] Failed to download clothing: HTTP {clothing_response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ [AvatarService] Failed to download clothing image: {str(e)}")
            else:
                logger.warning(f"⚠️ [AvatarService] No clothing URL generated from path: {clothing_path}")
            
            # Try to use Replicate API for high-quality virtual try-on
            logger.info(f"🔍 Checking Replicate availability: is_available={replicate_service.is_available()}, has_clothing_image={clothing_image is not None}")
            
            if replicate_service.is_available() and clothing_image:
                logger.info("🚀 Using Replicate API for virtual try-on")
                logger.info(f"🚀 Avatar image size: {avatar_image.size}, mode: {avatar_image.mode}")
                logger.info(f"🚀 Clothing image size: {clothing_image.size}, mode: {clothing_image.mode}")
                logger.info(f"🚀 Category: {category}")
                try:
                    # Generate a simple garment description from category and name
                    garment_description = f"{clothing_name} {category.replace('_', ' ')}" if clothing_name else f"a {category.replace('_', ' ')}"
                    
                    replicate_result = await replicate_service.create_virtual_tryon(
                        person_image=avatar_image,
                        garment_image=clothing_image,
                        category=category,
                        garment_description=garment_description
                    )
                    
                    logger.info(f"🚀 Replicate result received: {type(replicate_result)}, has image_base64: {replicate_result.get('image_base64')[:50] if replicate_result and replicate_result.get('image_base64') else 'None'}")
                    
                    if replicate_result and replicate_result.get("image_base64"):
                        image_base64_len = len(replicate_result["image_base64"])
                        logger.info(f"✅ Replicate virtual try-on successful! Image base64 length: {image_base64_len}")
                        return replicate_result["image_base64"]
                    else:
                        logger.warning("⚠️ Replicate returned no result, falling back to basic overlay")
                        logger.warning(f"⚠️ Replicate result: {replicate_result}")
                        
                except Exception as replicate_error:
                    logger.error(f"❌ Replicate API error: {str(replicate_error)}")
                    logger.error(f"❌ Error type: {type(replicate_error).__name__}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    logger.error("Falling back to basic overlay")
            else:
                if not replicate_service.is_available():
                    logger.warning("⚠️ Replicate service not available - using basic overlay")
                    logger.warning(f"⚠️ Replicate available check: {replicate_service.is_available()}")
                    logger.warning(f"⚠️ Replicate API token: {'Set' if replicate_service.api_token else 'Not set'}")
                else:
                    logger.warning("⚠️ No clothing image - using basic overlay")
                    logger.warning(f"⚠️ clothing_image is None or empty")
            
            # Fallback: Create virtual try-on using basic overlay
            result_image = avatar_image.copy()
            
            if clothing_image:
                logger.info("Using basic clothing overlay")
                result_image = self._simple_clothing_overlay(result_image, clothing_image, category)
            
            # Add subtle try-on indicator
            draw = ImageDraw.Draw(result_image)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Add small indicator in corner
            width, height = result_image.size
            indicator_text = f"Trying on: {clothing_name}"
            
            # Create semi-transparent background for text
            text_bbox = draw.textbbox((0, 0), indicator_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            overlay = Image.new('RGBA', (text_width + 20, text_height + 10), (0, 0, 0, 180))
            result_image.paste(overlay, (10, height - text_height - 20), overlay)
            
            draw.text((20, height - text_height - 15), indicator_text, fill='white', font=font)
            
            # Convert to base64
            buffer = io.BytesIO()
            result_image.save(buffer, format='PNG')
            base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return base64_string
            
        except Exception as e:
            logger.error(f"Error creating visual preview: {str(e)}")
            # Return original avatar as fallback
            try:
                response = requests.get(avatar_url)
                if response.status_code == 200:
                    return base64.b64encode(response.content).decode('utf-8')
            except Exception as fallback_error:
                logger.error(f"Fallback avatar download also failed: {str(fallback_error)}")
            
            # If all else fails, create a simple placeholder image
            try:
                from PIL import Image, ImageDraw, ImageFont
                import io
                
                # Create a simple placeholder
                placeholder = Image.new('RGB', (400, 600), (240, 240, 240))
                draw = ImageDraw.Draw(placeholder)
                
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
                except:
                    font = ImageFont.load_default()
                
                draw.text((50, 250), f"Trying on:", fill='black', font=font)
                draw.text((50, 300), clothing_name, fill='blue', font=font)
                draw.text((50, 350), f"({category})", fill='gray', font=font)
                
                buffer = io.BytesIO()
                placeholder.save(buffer, format='PNG')
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
                
            except Exception as placeholder_error:
                logger.error(f"Failed to create placeholder: {str(placeholder_error)}")
                return ""

    def _create_realistic_virtual_tryon(self, avatar_image: Image.Image, clothing_image: Image.Image, pose_keypoints: dict, category: str) -> Image.Image:
        """Create realistic virtual try-on using body segmentation and clothing warping"""
        try:
            logger.info(f"🎨 Creating realistic virtual try-on for {category}")
            
            # Step 1: Create body segmentation mask
            body_mask = self._create_body_mask(avatar_image)
            
            # Step 2: Extract body points from pose keypoints
            body_points = self._extract_body_points(pose_keypoints)
            
            # Step 3: Create clothing mask and warp it to fit body
            if body_mask and body_points:
                clothing_warped = self._warp_clothing_to_body(clothing_image, body_points, body_mask, avatar_image.size, category)
                
                if clothing_warped:
                    # Step 4: Blend clothing with avatar using body-aware masking
                    result = self._blend_clothing_with_avatar(avatar_image, clothing_warped, body_mask, category)
                    logger.info("✅ Realistic virtual try-on completed successfully")
                    return result
            
            # Fallback to pose-based approach if advanced method fails
            logger.warning("Advanced try-on failed, using pose-based approach")
            return self._overlay_clothing_on_avatar(avatar_image, clothing_image, pose_keypoints, category)
            
        except Exception as e:
            logger.error(f"Error in realistic virtual try-on: {str(e)}")
            # Fallback to pose-based approach
            return self._overlay_clothing_on_avatar(avatar_image, clothing_image, pose_keypoints, category)
    
    def _create_body_mask(self, avatar_image: Image.Image) -> Image.Image:
        """Create body segmentation mask using MediaPipe"""
        try:
            if not OPENCV_AVAILABLE:
                logger.warning("OpenCV not available - cannot create segmentation mask")
                return None
                
            if not self.selfie_segmentation:
                logger.warning("Selfie segmentation not available")
                return None
            
            # Convert PIL to cv2
            avatar_cv = cv2.cvtColor(np.array(avatar_image), cv2.COLOR_RGB2BGR)
            
            # Run segmentation
            results = self.selfie_segmentation.process(cv2.cvtColor(avatar_cv, cv2.COLOR_BGR2RGB))
            
            if results.segmentation_mask is None:
                logger.warning("No segmentation mask generated")
                return None
            
            # Convert mask to PIL Image
            mask_array = (results.segmentation_mask > 0.5).astype(np.uint8) * 255
            body_mask = Image.fromarray(mask_array, mode='L')
            
            # Resize to match avatar dimensions
            body_mask = body_mask.resize(avatar_image.size, Image.Resampling.LANCZOS)
            
            logger.info("✅ Body segmentation mask created successfully")
            return body_mask
            
        except Exception as e:
            logger.error(f"Error creating body mask: {str(e)}")
            return None
    
    def _warp_clothing_to_body(self, clothing_image: Image.Image, body_points: dict, body_mask: Image.Image, avatar_size: tuple, clothing_category: str) -> Image.Image:
        """Warp clothing to fit the person's body shape and pose"""
        try:
            avatar_width, avatar_height = avatar_size
            
            # Convert clothing to RGBA for transparency handling
            if clothing_image.mode != 'RGBA':
                clothing_image = clothing_image.convert('RGBA')
            
            # Define body regions for different clothing types
            if clothing_category.lower() in ['tops', 'shirts', 'sweaters', 'hoodies', 'jackets', 'outerwear']:
                region_points = self._get_torso_region_points(body_points, avatar_width, avatar_height)
                clothing_alpha = 200  # More opaque for tops
                
            elif clothing_category.lower() in ['bottoms', 'pants', 'jeans', 'shorts']:
                region_points = self._get_legs_region_points(body_points, avatar_width, avatar_height)
                clothing_alpha = 190  # Slightly transparent for bottoms
                
            elif clothing_category.lower() in ['dresses']:
                region_points = self._get_dress_region_points(body_points, avatar_width, avatar_height)
                clothing_alpha = 195
                
            else:
                # Default to torso region
                region_points = self._get_torso_region_points(body_points, avatar_width, avatar_height)
                clothing_alpha = 180
            
            if not region_points:
                logger.warning(f"Could not determine region points for {clothing_category}")
                return None
            
            # Warp clothing to fit the body region
            warped_clothing = self._apply_perspective_warp(clothing_image, region_points, avatar_size)
            
            if warped_clothing is None:
                logger.warning("Perspective warping failed")
                return None
            
            # Apply transparency
            warped_clothing.putalpha(clothing_alpha)
            
            logger.info(f"✅ Clothing warped successfully for {clothing_category}")
            return warped_clothing
            
        except Exception as e:
            logger.error(f"Error warping clothing: {str(e)}")
            return None
    
    def _get_torso_region_points(self, body_points: dict, width: int, height: int) -> list:
        """Get torso region points for clothing warping"""
        try:
            # Use shoulder and hip points to define torso region
            if not all(key in body_points for key in ['left_shoulder', 'right_shoulder']):
                return None
            
            left_shoulder = body_points['left_shoulder']
            right_shoulder = body_points['right_shoulder']
            
            # Estimate torso dimensions
            shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
            torso_height = int(height * 0.4)  # Torso is about 40% of body height
            
            # Define clothing region (slightly wider than shoulders)
            margin = int(shoulder_width * 0.2)
            top_y = max(0, left_shoulder[1] - int(shoulder_width * 0.1))  # Slightly above shoulders
            bottom_y = min(height, top_y + torso_height)
            
            left_x = max(0, left_shoulder[0] - margin)
            right_x = min(width, right_shoulder[0] + margin)
            
            # Return four corner points for perspective transformation
            return [
                (left_x, top_y),      # Top-left
                (right_x, top_y),     # Top-right
                (right_x, bottom_y),  # Bottom-right
                (left_x, bottom_y)    # Bottom-left
            ]
            
        except Exception as e:
            logger.error(f"Error getting torso region: {str(e)}")
            return None
    
    def _get_legs_region_points(self, body_points: dict, width: int, height: int) -> list:
        """Get legs region points for bottoms clothing warping"""
        try:
            # Use hip points to define legs region
            if not all(key in body_points for key in ['left_hip', 'right_hip']):
                return None
            
            left_hip = body_points['left_hip']
            right_hip = body_points['right_hip']
            
            # Define legs region
            hip_width = abs(right_hip[0] - left_hip[0])
            margin = int(hip_width * 0.1)
            
            top_y = left_hip[1]  # Start from hip level
            bottom_y = height  # Go to bottom of image
            
            left_x = max(0, left_hip[0] - margin)
            right_x = min(width, right_hip[0] + margin)
            
            return [
                (left_x, top_y),
                (right_x, top_y),
                (right_x, bottom_y),
                (left_x, bottom_y)
            ]
            
        except Exception as e:
            logger.error(f"Error getting legs region: {str(e)}")
            return None
    
    def _get_dress_region_points(self, body_points: dict, width: int, height: int) -> list:
        """Get dress region points combining torso and legs"""
        try:
            if not all(key in body_points for key in ['left_shoulder', 'right_shoulder']):
                return None
            
            left_shoulder = body_points['left_shoulder']
            right_shoulder = body_points['right_shoulder']
            
            shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
            margin = int(shoulder_width * 0.3)  # Dresses are wider
            
            top_y = max(0, left_shoulder[1] - int(shoulder_width * 0.1))
            bottom_y = height  # Dresses go to bottom
            
            left_x = max(0, left_shoulder[0] - margin)
            right_x = min(width, right_shoulder[0] + margin)
            
            return [
                (left_x, top_y),
                (right_x, top_y),
                (right_x, bottom_y),
                (left_x, bottom_y)
            ]
            
        except Exception as e:
            logger.error(f"Error getting dress region: {str(e)}")
            return None
    
    def _apply_perspective_warp(self, clothing_image: Image.Image, region_points: list, target_size: tuple) -> Image.Image:
        """Apply perspective transformation to warp clothing to body region"""
        try:
            if not OPENCV_AVAILABLE:
                logger.warning("OpenCV not available - cannot apply perspective warp")
                return clothing_image
                
            # Convert PIL to OpenCV
            clothing_cv = cv2.cvtColor(np.array(clothing_image), cv2.COLOR_RGBA2BGRA)
            
            # Define source points (corners of clothing image)
            h, w = clothing_cv.shape[:2]
            src_points = np.float32([
                [0, 0],      # Top-left
                [w, 0],      # Top-right
                [w, h],      # Bottom-right
                [0, h]       # Bottom-left
            ])
            
            # Define destination points (body region)
            dst_points = np.float32(region_points)
            
            # Calculate perspective transformation matrix
            matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            
            # Apply perspective warp
            warped_cv = cv2.warpPerspective(
                clothing_cv, 
                matrix, 
                target_size,
                flags=cv2.INTER_LANCZOS4,
                borderMode=cv2.BORDER_TRANSPARENT
            )
            
            # Convert back to PIL
            warped_pil = Image.fromarray(cv2.cvtColor(warped_cv, cv2.COLOR_BGRA2RGBA))
            
            logger.info("✅ Perspective warp applied successfully")
            return warped_pil
            
        except Exception as e:
            logger.error(f"Error applying perspective warp: {str(e)}")
            return None
    
    def _blend_clothing_with_avatar(self, avatar_image: Image.Image, clothing_warped: Image.Image, body_mask: Image.Image, clothing_category: str) -> Image.Image:
        """Blend warped clothing with avatar using body-aware masking"""
        try:
            # Convert avatar to RGBA
            result = avatar_image.convert('RGBA')
            
            # Create clothing mask based on body mask and clothing category
            clothing_mask = self._create_clothing_mask(body_mask, clothing_category, avatar_image.size)
            
            # Apply clothing mask to warped clothing
            if clothing_mask:
                # Convert mask to alpha channel
                clothing_alpha = clothing_warped.split()[-1]  # Get alpha channel
                combined_alpha = Image.composite(clothing_alpha, Image.new('L', clothing_alpha.size, 0), clothing_mask)
                clothing_warped.putalpha(combined_alpha)
            
            # Blend using alpha composite for natural look
            result = Image.alpha_composite(result, clothing_warped)
            
            logger.info(f"✅ Clothing blended successfully with avatar for {clothing_category}")
            return result.convert('RGB')
            
        except Exception as e:
            logger.error(f"Error blending clothing with avatar: {str(e)}")
            return avatar_image
    
    def _create_clothing_mask(self, body_mask: Image.Image, clothing_category: str, image_size: tuple) -> Image.Image:
        """Create clothing-specific mask based on body segmentation"""
        try:
            width, height = image_size
            
            # Convert body mask to numpy for processing
            mask_array = np.array(body_mask)
            
            # Create clothing-specific mask
            clothing_mask = np.zeros_like(mask_array)
            
            if clothing_category.lower() in ['tops', 'shirts', 'sweaters', 'hoodies', 'jackets', 'outerwear']:
                # Mask for upper body (top 60% of body mask)
                body_pixels = np.where(mask_array > 128)
                if len(body_pixels[0]) > 0:
                    min_y = np.min(body_pixels[0])
                    max_y = np.max(body_pixels[0])
                    torso_cutoff = min_y + int((max_y - min_y) * 0.6)
                    
                    # Apply mask to upper portion
                    clothing_mask[min_y:torso_cutoff] = mask_array[min_y:torso_cutoff]
                    
            elif clothing_category.lower() in ['bottoms', 'pants', 'jeans', 'shorts']:
                # Mask for lower body (bottom 60% of body mask)
                body_pixels = np.where(mask_array > 128)
                if len(body_pixels[0]) > 0:
                    min_y = np.min(body_pixels[0])
                    max_y = np.max(body_pixels[0])
                    legs_cutoff = min_y + int((max_y - min_y) * 0.4)
                    
                    # Apply mask to lower portion
                    clothing_mask[legs_cutoff:max_y] = mask_array[legs_cutoff:max_y]
                    
            else:
                # For dresses and other items, use full body mask
                clothing_mask = mask_array
            
            return Image.fromarray(clothing_mask, mode='L')
            
        except Exception as e:
            logger.error(f"Error creating clothing mask: {str(e)}")
            return body_mask  # Fallback to full body mask

    def _overlay_clothing_on_avatar(self, avatar_image: Image.Image, clothing_image: Image.Image, pose_keypoints: dict, category: str) -> Image.Image:
        """Overlay clothing item on avatar using pose keypoints for positioning"""
        try:
            from PIL import Image, ImageDraw
            import numpy as np
            
            # Create a copy of the avatar to work with
            result = avatar_image.copy().convert('RGBA')
            avatar_width, avatar_height = result.size
            
            # Extract pose keypoints if available
            keypoints = None
            if pose_keypoints and 'keypoints' in pose_keypoints:
                keypoints = pose_keypoints['keypoints']
            
            if not keypoints:
                logger.warning("No pose keypoints available for clothing overlay")
                return self._simple_clothing_overlay(result, clothing_image, category)
            
            # Get key body points for clothing positioning
            body_points = self._extract_body_points(keypoints, avatar_width, avatar_height)
            
            if not body_points:
                logger.warning("Could not extract body points from pose data")
                return self._simple_clothing_overlay(result, clothing_image, category)
            
            # Position and resize clothing based on category and body points
            if category.lower() in ['tops', 'shirts', 'sweaters', 'hoodies', 'jackets']:
                overlay_image = self._position_top_clothing(clothing_image, body_points, avatar_width, avatar_height)
            elif category.lower() in ['bottoms', 'pants', 'jeans', 'shorts']:
                overlay_image = self._position_bottom_clothing(clothing_image, body_points, avatar_width, avatar_height)
            elif category.lower() in ['dresses']:
                overlay_image = self._position_dress(clothing_image, body_points, avatar_width, avatar_height)
            else:
                # Default positioning
                overlay_image = self._simple_clothing_overlay(result, clothing_image, category)
                return overlay_image
            
            # Blend the clothing onto the avatar
            if overlay_image:
                # Apply some transparency for realistic blending
                overlay_image.putalpha(200)  # Make slightly transparent
                result.paste(overlay_image, (0, 0), overlay_image)
            
            return result.convert('RGB')
            
        except Exception as e:
            logger.error(f"Error overlaying clothing on avatar: {str(e)}")
            return self._simple_clothing_overlay(avatar_image, clothing_image, category)
    
    def _extract_body_points(self, keypoints: list, img_width: int, img_height: int) -> dict:
        """Extract key body points from MediaPipe pose keypoints"""
        try:
            logger.info(f"🔍 Keypoints data structure: type={type(keypoints)}, length={len(keypoints) if hasattr(keypoints, '__len__') else 'N/A'}")
            if keypoints and len(keypoints) > 0:
                logger.info(f"🔍 First keypoint sample: {keypoints[0] if len(keypoints) > 0 else 'None'}")
            
            # MediaPipe pose landmark indices
            # 0: nose, 11: left_shoulder, 12: right_shoulder
            # 23: left_hip, 24: right_hip, 25: left_knee, 26: right_knee
            
            if not keypoints or len(keypoints) < 33:  # MediaPipe has 33 landmarks
                logger.warning(f"Insufficient keypoints: {len(keypoints) if keypoints else 0} < 33")
                return None
            
            points = {}
            
            # Extract key points (coordinates are already in pixel values, not normalized)
            try:
                # Left shoulder (index 11)
                if len(keypoints) > 11 and keypoints[11] and 'x' in keypoints[11] and 'y' in keypoints[11]:
                    points['left_shoulder'] = (int(keypoints[11]['x']), int(keypoints[11]['y']))
                    logger.info(f"✅ Left shoulder: {points['left_shoulder']}")
                
                # Right shoulder (index 12)
                if len(keypoints) > 12 and keypoints[12] and 'x' in keypoints[12] and 'y' in keypoints[12]:
                    points['right_shoulder'] = (int(keypoints[12]['x']), int(keypoints[12]['y']))
                    logger.info(f"✅ Right shoulder: {points['right_shoulder']}")
                
                # Left hip (index 23)
                if len(keypoints) > 23 and keypoints[23] and 'x' in keypoints[23] and 'y' in keypoints[23]:
                    points['left_hip'] = (int(keypoints[23]['x']), int(keypoints[23]['y']))
                    logger.info(f"✅ Left hip: {points['left_hip']}")
                
                # Right hip (index 24)
                if len(keypoints) > 24 and keypoints[24] and 'x' in keypoints[24] and 'y' in keypoints[24]:
                    points['right_hip'] = (int(keypoints[24]['x']), int(keypoints[24]['y']))
                    logger.info(f"✅ Right hip: {points['right_hip']}")
                    
            except (IndexError, TypeError, ValueError, KeyError) as e:
                logger.error(f"Error accessing keypoint data: {str(e)}")
                return None
            
            logger.info(f"🎯 Extracted {len(points)} body points: {list(points.keys())}")
            return points if len(points) >= 2 else None
            
        except Exception as e:
            logger.error(f"Error extracting body points: {str(e)}")
            return None
    
    def _position_top_clothing(self, clothing_image: Image.Image, body_points: dict, avatar_width: int, avatar_height: int) -> Image.Image:
        """Position top clothing (shirts, sweaters, etc.) on the avatar"""
        try:
            if 'left_shoulder' not in body_points or 'right_shoulder' not in body_points:
                return None
            
            # Calculate torso dimensions
            left_shoulder = body_points['left_shoulder']
            right_shoulder = body_points['right_shoulder']
            
            # Calculate clothing size based on shoulder width
            shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
            clothing_width = int(shoulder_width * 1.2)  # Slightly wider than shoulders
            
            # Estimate torso height (shoulder to hip)
            if 'left_hip' in body_points:
                torso_height = abs(body_points['left_hip'][1] - left_shoulder[1])
            else:
                torso_height = int(avatar_height * 0.4)  # Estimate
            
            # Resize clothing to fit torso
            clothing_resized = clothing_image.resize((clothing_width, torso_height), Image.Resampling.LANCZOS)
            
            # Create overlay canvas
            overlay = Image.new('RGBA', (avatar_width, avatar_height), (0, 0, 0, 0))
            
            # Position clothing at torso center
            center_x = (left_shoulder[0] + right_shoulder[0]) // 2
            paste_x = center_x - clothing_width // 2
            paste_y = left_shoulder[1]
            
            # Ensure clothing stays within avatar bounds
            paste_x = max(0, min(paste_x, avatar_width - clothing_width))
            paste_y = max(0, min(paste_y, avatar_height - torso_height))
            
            overlay.paste(clothing_resized, (paste_x, paste_y), clothing_resized)
            
            return overlay
            
        except Exception as e:
            logger.error(f"Error positioning top clothing: {str(e)}")
            return None
    
    def _position_bottom_clothing(self, clothing_image: Image.Image, body_points: dict, avatar_width: int, avatar_height: int) -> Image.Image:
        """Position bottom clothing (pants, shorts, etc.) on the avatar"""
        try:
            if 'left_hip' not in body_points or 'right_hip' not in body_points:
                return None
            
            # Calculate hip dimensions
            left_hip = body_points['left_hip']
            right_hip = body_points['right_hip']
            
            # Calculate clothing size based on hip width
            hip_width = abs(right_hip[0] - left_hip[0])
            clothing_width = int(hip_width * 1.1)  # Slightly wider than hips
            
            # Estimate leg height (hip to bottom of image)
            leg_height = avatar_height - left_hip[1]
            
            # Resize clothing to fit legs
            clothing_resized = clothing_image.resize((clothing_width, leg_height), Image.Resampling.LANCZOS)
            
            # Create overlay canvas
            overlay = Image.new('RGBA', (avatar_width, avatar_height), (0, 0, 0, 0))
            
            # Position clothing at hip center
            center_x = (left_hip[0] + right_hip[0]) // 2
            paste_x = center_x - clothing_width // 2
            paste_y = left_hip[1]
            
            # Ensure clothing stays within avatar bounds
            paste_x = max(0, min(paste_x, avatar_width - clothing_width))
            paste_y = max(0, min(paste_y, avatar_height - leg_height))
            
            overlay.paste(clothing_resized, (paste_x, paste_y), clothing_resized)
            
            return overlay
            
        except Exception as e:
            logger.error(f"Error positioning bottom clothing: {str(e)}")
            return None
    
    def _position_dress(self, clothing_image: Image.Image, body_points: dict, avatar_width: int, avatar_height: int) -> Image.Image:
        """Position dress on the avatar"""
        try:
            if 'left_shoulder' not in body_points or 'right_shoulder' not in body_points:
                return None
            
            # Use shoulder width for dress width
            left_shoulder = body_points['left_shoulder']
            right_shoulder = body_points['right_shoulder']
            shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
            clothing_width = int(shoulder_width * 1.3)  # Dresses are typically wider
            
            # Dress height from shoulders to bottom
            dress_height = avatar_height - left_shoulder[1]
            
            # Resize dress
            clothing_resized = clothing_image.resize((clothing_width, dress_height), Image.Resampling.LANCZOS)
            
            # Create overlay canvas
            overlay = Image.new('RGBA', (avatar_width, avatar_height), (0, 0, 0, 0))
            
            # Position dress at shoulder center
            center_x = (left_shoulder[0] + right_shoulder[0]) // 2
            paste_x = center_x - clothing_width // 2
            paste_y = left_shoulder[1]
            
            # Ensure dress stays within avatar bounds
            paste_x = max(0, min(paste_x, avatar_width - clothing_width))
            paste_y = max(0, min(paste_y, avatar_height - dress_height))
            
            overlay.paste(clothing_resized, (paste_x, paste_y), clothing_resized)
            
            return overlay
            
        except Exception as e:
            logger.error(f"Error positioning dress: {str(e)}")
            return None
    
    def _simple_clothing_overlay(self, avatar_image: Image.Image, clothing_image: Image.Image, category: str) -> Image.Image:
        """Simple clothing overlay when pose data is not available - more realistic positioning"""
        try:
            logger.info(f"🎨 Using simple overlay for {category} clothing")
            avatar_width, avatar_height = avatar_image.size
            
            # More realistic positioning based on category
            if category.lower() in ['tops', 'shirts', 'sweaters', 'hoodies', 'jackets']:
                # Position in upper torso area - more fitted
                clothing_width = int(avatar_width * 0.7)  # Wider coverage
                clothing_height = int(avatar_height * 0.45)  # Taller for better torso coverage
                paste_x = int(avatar_width * 0.15)  # Slightly more centered
                paste_y = int(avatar_height * 0.15)  # Higher up for better chest coverage
                alpha = 180  # More opaque for tops
                
            elif category.lower() in ['bottoms', 'pants', 'jeans', 'shorts']:
                # Position in lower body area - from waist down
                clothing_width = int(avatar_width * 0.6)
                clothing_height = int(avatar_height * 0.5)  # Longer for full leg coverage
                paste_x = int(avatar_width * 0.2)
                paste_y = int(avatar_height * 0.45)  # Start from waist area
                alpha = 170  # Slightly transparent
                
            elif category.lower() in ['dresses']:
                # Full body coverage for dresses
                clothing_width = int(avatar_width * 0.75)
                clothing_height = int(avatar_height * 0.7)  # Most of the body
                paste_x = int(avatar_width * 0.125)
                paste_y = int(avatar_height * 0.15)  # From chest down
                alpha = 175
                
            else:
                # Default center positioning
                clothing_width = int(avatar_width * 0.6)
                clothing_height = int(avatar_height * 0.5)
                paste_x = int(avatar_width * 0.2)
                paste_y = int(avatar_height * 0.25)
                alpha = 160
            
            # Resize clothing with better quality
            clothing_resized = clothing_image.resize((clothing_width, clothing_height), Image.Resampling.LANCZOS)
            
            # Create overlay with appropriate transparency
            overlay = Image.new('RGBA', (avatar_width, avatar_height), (0, 0, 0, 0))
            
            # Apply transparency to clothing
            if clothing_resized.mode != 'RGBA':
                clothing_resized = clothing_resized.convert('RGBA')
            clothing_resized.putalpha(alpha)
            
            # Paste clothing onto overlay
            overlay.paste(clothing_resized, (paste_x, paste_y), clothing_resized)
            
            # Blend with avatar using better blending
            result = avatar_image.convert('RGBA')
            result = Image.alpha_composite(result, overlay)
            
            logger.info(f"✅ Applied simple overlay: {clothing_width}x{clothing_height} at ({paste_x}, {paste_y})")
            return result.convert('RGB')
            
        except Exception as e:
            logger.error(f"Error in simple clothing overlay: {str(e)}")
            return avatar_image

    def get_service_status(self) -> Dict:
        """Get service status and capabilities"""
        return {
            "available": self.is_available(),
            "mediapipe_installed": MEDIAPIPE_AVAILABLE,
            "pose_detector_ready": self.pose_detector is not None,
            "segmentation_ready": self.selfie_segmentation is not None,
            "max_workers": self.executor._max_workers if self.executor else 0,
            "supported_formats": ["JPEG", "PNG", "WebP"],
            "max_image_size": "10MB"
        }


# Create singleton instance
avatar_service = AvatarService()
