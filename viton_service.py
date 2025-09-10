"""
Advanced Virtual Try-On Service using ViTON-style approach
Inspired by SwayamInSync/clothes-virtual-try-on repository
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import torch
import torch.nn.functional as F
from torchvision import transforms
from skimage import morphology
from rembg import remove
import logging
import io
import base64
from typing import Optional, Dict, Tuple, List
import mediapipe as mp

logger = logging.getLogger(__name__)

class AdvancedVitonService:
    """Advanced Virtual Try-On Service using deep learning techniques"""
    
    def __init__(self):
        """Initialize the ViTON service with required models"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Initialize MediaPipe components
        self._init_mediapipe()
        
        # Transform for image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize((512, 384)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        # Reverse transform for visualization
        self.reverse_transform = transforms.Compose([
            transforms.Normalize([-0.485/0.229, -0.456/0.224, -0.406/0.225], 
                               [1/0.229, 1/0.224, 1/0.225]),
            transforms.ToPILImage()
        ])
        
        logger.info("AdvancedVitonService initialized successfully")
    
    def _init_mediapipe(self):
        """Initialize MediaPipe components"""
        try:
            # Pose detection
            self.mp_pose = mp.solutions.pose
            self.pose_detector = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=True,
                min_detection_confidence=0.5
            )
            
            # Selfie segmentation for body parsing
            self.mp_selfie_segmentation = mp.solutions.selfie_segmentation
            self.selfie_segmentation = self.mp_selfie_segmentation.SelfieSegmentation(
                model_selection=1
            )
            
            logger.info("MediaPipe components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe: {str(e)}")
            self.pose_detector = None
            self.selfie_segmentation = None
    
    def is_available(self) -> bool:
        """Check if the service is available"""
        return (self.pose_detector is not None and 
                self.selfie_segmentation is not None)
    
    def create_virtual_tryon(self, person_image: Image.Image, clothing_image: Image.Image, 
                           clothing_category: str = "tops") -> Optional[str]:
        """
        Create realistic virtual try-on using ViTON-style approach
        
        Args:
            person_image: PIL Image of the person
            clothing_image: PIL Image of the clothing item
            clothing_category: Category of clothing (tops, bottoms, dresses)
            
        Returns:
            Base64 encoded result image or None if failed
        """
        try:
            logger.info(f"🎨 Creating advanced virtual try-on for {clothing_category}")
            
            # Step 1: Preprocess images
            person_processed = self._preprocess_person_image(person_image)
            clothing_processed = self._preprocess_clothing_image(clothing_image)
            
            if person_processed is None or clothing_processed is None:
                logger.error("Failed to preprocess images")
                return None
            
            # Step 2: Generate person representation
            person_representation = self._generate_person_representation(person_processed)
            
            if person_representation is None:
                logger.error("Failed to generate person representation")
                return None
            
            # Step 3: Generate clothing mask
            clothing_mask = self._generate_clothing_mask(clothing_processed)
            
            # Step 4: Perform geometric matching
            warped_clothing = self._geometric_matching_module(
                clothing_processed, clothing_mask, person_representation, clothing_category
            )
            
            if warped_clothing is None:
                logger.error("Geometric matching failed")
                return None
            
            # Step 5: Try-on synthesis
            result_image = self._tryon_synthesis_module(
                person_processed, warped_clothing, person_representation, clothing_category
            )
            
            if result_image is None:
                logger.error("Try-on synthesis failed")
                return None
            
            # Step 6: Post-process and convert to base64
            result_base64 = self._postprocess_result(result_image)
            
            logger.info("✅ Advanced virtual try-on completed successfully")
            return result_base64
            
        except Exception as e:
            logger.error(f"Error in virtual try-on: {str(e)}")
            return None
    
    def _preprocess_person_image(self, image: Image.Image) -> Optional[Image.Image]:
        """Preprocess person image for virtual try-on"""
        try:
            # Resize to standard size
            image = image.resize((384, 512), Image.Resampling.LANCZOS)
            
            # Ensure RGB format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            logger.error(f"Error preprocessing person image: {str(e)}")
            return None
    
    def _preprocess_clothing_image(self, image: Image.Image) -> Optional[Image.Image]:
        """Preprocess clothing image for virtual try-on"""
        try:
            # Remove background from clothing
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            
            # Use rembg to remove background
            no_bg_bytes = remove(image_bytes.getvalue())
            clothing_no_bg = Image.open(io.BytesIO(no_bg_bytes))
            
            # Resize to standard size
            clothing_no_bg = clothing_no_bg.resize((384, 512), Image.Resampling.LANCZOS)
            
            # Convert to RGB (background will be white)
            if clothing_no_bg.mode == 'RGBA':
                # Create white background
                white_bg = Image.new('RGB', clothing_no_bg.size, (255, 255, 255))
                white_bg.paste(clothing_no_bg, mask=clothing_no_bg.split()[-1])
                clothing_no_bg = white_bg
            
            return clothing_no_bg
            
        except Exception as e:
            logger.error(f"Error preprocessing clothing image: {str(e)}")
            return None
    
    def _generate_person_representation(self, person_image: Image.Image) -> Optional[Dict]:
        """Generate comprehensive person representation including pose and body parsing"""
        try:
            # Convert PIL to OpenCV
            person_cv = cv2.cvtColor(np.array(person_image), cv2.COLOR_RGB2BGR)
            
            # Get pose landmarks
            pose_results = self.pose_detector.process(cv2.cvtColor(person_cv, cv2.COLOR_BGR2RGB))
            
            # Get body segmentation
            segmentation_results = self.selfie_segmentation.process(cv2.cvtColor(person_cv, cv2.COLOR_BGR2RGB))
            
            if pose_results.pose_landmarks is None or segmentation_results.segmentation_mask is None:
                logger.warning("Failed to detect pose or segmentation")
                return None
            
            # Extract pose keypoints
            pose_keypoints = []
            for landmark in pose_results.pose_landmarks.landmark:
                pose_keypoints.append([
                    landmark.x * person_image.width,
                    landmark.y * person_image.height,
                    landmark.visibility
                ])
            
            # Create body mask
            body_mask = (segmentation_results.segmentation_mask > 0.5).astype(np.uint8) * 255
            body_mask_pil = Image.fromarray(body_mask, mode='L')
            
            # Create body parsing (simplified version)
            body_parsing = self._create_body_parsing(pose_keypoints, person_image.size)
            
            # Create pose map
            pose_map = self._create_pose_map(pose_keypoints, person_image.size)
            
            return {
                'pose_keypoints': pose_keypoints,
                'body_mask': body_mask_pil,
                'body_parsing': body_parsing,
                'pose_map': pose_map,
                'original_image': person_image
            }
            
        except Exception as e:
            logger.error(f"Error generating person representation: {str(e)}")
            return None
    
    def _create_body_parsing(self, pose_keypoints: List, image_size: Tuple[int, int]) -> Image.Image:
        """Create simplified body parsing map"""
        try:
            width, height = image_size
            parsing_map = np.zeros((height, width), dtype=np.uint8)
            
            # Define body part regions based on pose keypoints
            # This is a simplified version - in a full implementation, 
            # you would use a trained body parsing model
            
            if len(pose_keypoints) >= 33:  # MediaPipe pose has 33 landmarks
                # Head region
                nose = pose_keypoints[0]
                if nose[2] > 0.5:  # visibility check
                    head_center = (int(nose[0]), int(nose[1]))
                    cv2.circle(parsing_map, head_center, 30, 1, -1)  # Head = 1
                
                # Torso region
                left_shoulder = pose_keypoints[11]
                right_shoulder = pose_keypoints[12]
                left_hip = pose_keypoints[23]
                right_hip = pose_keypoints[24]
                
                if all(kp[2] > 0.5 for kp in [left_shoulder, right_shoulder, left_hip, right_hip]):
                    # Create torso polygon
                    torso_points = np.array([
                        [int(left_shoulder[0]), int(left_shoulder[1])],
                        [int(right_shoulder[0]), int(right_shoulder[1])],
                        [int(right_hip[0]), int(right_hip[1])],
                        [int(left_hip[0]), int(left_hip[1])]
                    ])
                    cv2.fillPoly(parsing_map, [torso_points], 2)  # Torso = 2
                
                # Arms
                if left_shoulder[2] > 0.5 and pose_keypoints[15][2] > 0.5:  # left wrist
                    cv2.line(parsing_map, 
                            (int(left_shoulder[0]), int(left_shoulder[1])),
                            (int(pose_keypoints[15][0]), int(pose_keypoints[15][1])), 
                            3, 15)  # Left arm = 3
                
                if right_shoulder[2] > 0.5 and pose_keypoints[16][2] > 0.5:  # right wrist
                    cv2.line(parsing_map, 
                            (int(right_shoulder[0]), int(right_shoulder[1])),
                            (int(pose_keypoints[16][0]), int(pose_keypoints[16][1])), 
                            4, 15)  # Right arm = 4
                
                # Legs
                if left_hip[2] > 0.5 and pose_keypoints[31][2] > 0.5:  # left ankle
                    cv2.line(parsing_map, 
                            (int(left_hip[0]), int(left_hip[1])),
                            (int(pose_keypoints[31][0]), int(pose_keypoints[31][1])), 
                            5, 20)  # Left leg = 5
                
                if right_hip[2] > 0.5 and pose_keypoints[32][2] > 0.5:  # right ankle
                    cv2.line(parsing_map, 
                            (int(right_hip[0]), int(right_hip[1])),
                            (int(pose_keypoints[32][0]), int(pose_keypoints[32][1])), 
                            6, 20)  # Right leg = 6
            
            return Image.fromarray(parsing_map, mode='L')
            
        except Exception as e:
            logger.error(f"Error creating body parsing: {str(e)}")
            return Image.new('L', image_size, 0)
    
    def _create_pose_map(self, pose_keypoints: List, image_size: Tuple[int, int]) -> Image.Image:
        """Create pose heatmap"""
        try:
            width, height = image_size
            pose_map = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Draw pose skeleton
            connections = [
                # Body
                (11, 12), (11, 13), (12, 14), (13, 15), (14, 16),  # Arms
                (11, 23), (12, 24), (23, 24),  # Torso
                (23, 25), (24, 26), (25, 27), (26, 28),  # Legs
                (27, 29), (28, 30), (29, 31), (30, 32),  # Feet
                # Head
                (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8)
            ]
            
            # Draw connections
            for connection in connections:
                if (connection[0] < len(pose_keypoints) and 
                    connection[1] < len(pose_keypoints)):
                    
                    kp1 = pose_keypoints[connection[0]]
                    kp2 = pose_keypoints[connection[1]]
                    
                    if kp1[2] > 0.5 and kp2[2] > 0.5:  # visibility check
                        cv2.line(pose_map,
                                (int(kp1[0]), int(kp1[1])),
                                (int(kp2[0]), int(kp2[1])),
                                (255, 255, 255), 3)
            
            # Draw keypoints
            for kp in pose_keypoints:
                if kp[2] > 0.5:  # visibility check
                    cv2.circle(pose_map, (int(kp[0]), int(kp[1])), 5, (0, 255, 0), -1)
            
            return Image.fromarray(pose_map)
            
        except Exception as e:
            logger.error(f"Error creating pose map: {str(e)}")
            return Image.new('RGB', image_size, (0, 0, 0))
    
    def _generate_clothing_mask(self, clothing_image: Image.Image) -> Image.Image:
        """Generate clothing mask"""
        try:
            # Convert to grayscale
            gray = clothing_image.convert('L')
            
            # Create mask based on non-white pixels
            mask_array = np.array(gray)
            mask_array = (mask_array < 240).astype(np.uint8) * 255
            
            # Morphological operations to clean up the mask
            kernel = np.ones((3, 3), np.uint8)
            mask_array = cv2.morphologyEx(mask_array, cv2.MORPH_CLOSE, kernel)
            mask_array = cv2.morphologyEx(mask_array, cv2.MORPH_OPEN, kernel)
            
            return Image.fromarray(mask_array, mode='L')
            
        except Exception as e:
            logger.error(f"Error generating clothing mask: {str(e)}")
            return Image.new('L', clothing_image.size, 0)
    
    def _geometric_matching_module(self, clothing_image: Image.Image, clothing_mask: Image.Image,
                                 person_representation: Dict, clothing_category: str) -> Optional[Image.Image]:
        """Geometric Matching Module - warp clothing to fit person's pose"""
        try:
            # Get target region based on clothing category
            target_region = self._get_target_region(person_representation, clothing_category)
            
            if target_region is None:
                logger.warning("Could not determine target region")
                return None
            
            # Perform Thin Plate Spline (TPS) transformation
            warped_clothing = self._tps_transformation(
                clothing_image, clothing_mask, target_region
            )
            
            return warped_clothing
            
        except Exception as e:
            logger.error(f"Error in geometric matching: {str(e)}")
            return None
    
    def _get_target_region(self, person_representation: Dict, clothing_category: str) -> Optional[np.ndarray]:
        """Get target region on person for clothing placement"""
        try:
            pose_keypoints = person_representation['pose_keypoints']
            image_size = person_representation['original_image'].size
            
            if clothing_category.lower() in ['tops', 'shirts', 'sweaters', 'hoodies', 'jackets']:
                # Target torso region
                if len(pose_keypoints) >= 25:
                    left_shoulder = pose_keypoints[11]
                    right_shoulder = pose_keypoints[12]
                    left_hip = pose_keypoints[23]
                    right_hip = pose_keypoints[24]
                    
                    if all(kp[2] > 0.5 for kp in [left_shoulder, right_shoulder, left_hip, right_hip]):
                        return np.array([
                            [left_shoulder[0], left_shoulder[1]],
                            [right_shoulder[0], right_shoulder[1]],
                            [right_hip[0], right_hip[1]],
                            [left_hip[0], left_hip[1]]
                        ])
            
            elif clothing_category.lower() in ['bottoms', 'pants', 'jeans', 'shorts']:
                # Target legs region
                if len(pose_keypoints) >= 33:
                    left_hip = pose_keypoints[23]
                    right_hip = pose_keypoints[24]
                    left_ankle = pose_keypoints[31]
                    right_ankle = pose_keypoints[32]
                    
                    if all(kp[2] > 0.5 for kp in [left_hip, right_hip, left_ankle, right_ankle]):
                        return np.array([
                            [left_hip[0], left_hip[1]],
                            [right_hip[0], right_hip[1]],
                            [right_ankle[0], right_ankle[1]],
                            [left_ankle[0], left_ankle[1]]
                        ])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting target region: {str(e)}")
            return None
    
    def _tps_transformation(self, clothing_image: Image.Image, clothing_mask: Image.Image,
                          target_region: np.ndarray) -> Optional[Image.Image]:
        """Apply Thin Plate Spline transformation for clothing warping"""
        try:
            # Simplified TPS transformation using perspective transformation
            # In a full implementation, you would use proper TPS
            
            clothing_cv = cv2.cvtColor(np.array(clothing_image), cv2.COLOR_RGB2BGR)
            h, w = clothing_cv.shape[:2]
            
            # Source points (corners of clothing)
            src_points = np.float32([
                [0, 0], [w, 0], [w, h], [0, h]
            ])
            
            # Destination points (target region on person)
            dst_points = target_region.astype(np.float32)
            
            # Calculate perspective transformation matrix
            matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            
            # Apply transformation
            warped = cv2.warpPerspective(
                clothing_cv, matrix, (384, 512),
                flags=cv2.INTER_LANCZOS4,
                borderMode=cv2.BORDER_TRANSPARENT
            )
            
            # Convert back to PIL
            warped_pil = Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB))
            
            return warped_pil
            
        except Exception as e:
            logger.error(f"Error in TPS transformation: {str(e)}")
            return None
    
    def _tryon_synthesis_module(self, person_image: Image.Image, warped_clothing: Image.Image,
                              person_representation: Dict, clothing_category: str) -> Optional[Image.Image]:
        """Try-On Synthesis Module - blend warped clothing with person"""
        try:
            # Get body parsing and create clothing region mask
            body_parsing = person_representation['body_parsing']
            body_mask = person_representation['body_mask']
            
            # Create clothing region mask based on category
            clothing_region_mask = self._create_clothing_region_mask(
                body_parsing, clothing_category, person_image.size
            )
            
            # Blend clothing with person
            result = self._blend_with_person(
                person_image, warped_clothing, clothing_region_mask, body_mask
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in try-on synthesis: {str(e)}")
            return None
    
    def _create_clothing_region_mask(self, body_parsing: Image.Image, clothing_category: str,
                                   image_size: Tuple[int, int]) -> Image.Image:
        """Create mask for clothing region based on body parsing"""
        try:
            parsing_array = np.array(body_parsing)
            mask = np.zeros_like(parsing_array)
            
            if clothing_category.lower() in ['tops', 'shirts', 'sweaters', 'hoodies', 'jackets']:
                # Include torso and arms
                mask[(parsing_array == 2) | (parsing_array == 3) | (parsing_array == 4)] = 255
                
            elif clothing_category.lower() in ['bottoms', 'pants', 'jeans', 'shorts']:
                # Include legs
                mask[(parsing_array == 5) | (parsing_array == 6)] = 255
                
            elif clothing_category.lower() in ['dresses']:
                # Include torso, arms, and upper legs
                mask[(parsing_array == 2) | (parsing_array == 3) | 
                     (parsing_array == 4) | (parsing_array == 5) | (parsing_array == 6)] = 255
            
            # Apply morphological operations to smooth the mask
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            return Image.fromarray(mask, mode='L')
            
        except Exception as e:
            logger.error(f"Error creating clothing region mask: {str(e)}")
            return Image.new('L', image_size, 0)
    
    def _blend_with_person(self, person_image: Image.Image, warped_clothing: Image.Image,
                          clothing_mask: Image.Image, body_mask: Image.Image) -> Image.Image:
        """Blend warped clothing with person image"""
        try:
            # Convert all to RGBA
            person_rgba = person_image.convert('RGBA')
            clothing_rgba = warped_clothing.convert('RGBA')
            
            # Create composite mask
            clothing_mask_array = np.array(clothing_mask)
            body_mask_array = np.array(body_mask)
            
            # Combine masks - only apply clothing where both body and clothing region exist
            composite_mask = np.minimum(clothing_mask_array, body_mask_array)
            
            # Apply Gaussian blur for smooth blending
            composite_mask = cv2.GaussianBlur(composite_mask, (5, 5), 0)
            composite_mask_pil = Image.fromarray(composite_mask, mode='L')
            
            # Use the mask to blend images
            result = Image.composite(clothing_rgba, person_rgba, composite_mask_pil)
            
            return result.convert('RGB')
            
        except Exception as e:
            logger.error(f"Error blending with person: {str(e)}")
            return person_image
    
    def _postprocess_result(self, result_image: Image.Image) -> str:
        """Post-process result and convert to base64"""
        try:
            # Apply final enhancements
            # Slight sharpening
            result_image = result_image.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            
            # Convert to base64
            buffer = io.BytesIO()
            result_image.save(buffer, format='PNG', quality=95)
            base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return base64_string
            
        except Exception as e:
            logger.error(f"Error post-processing result: {str(e)}")
            return ""


# Create singleton instance
advanced_viton_service = AdvancedVitonService()
