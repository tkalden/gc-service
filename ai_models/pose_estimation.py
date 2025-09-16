"""
Pose Estimation Module for Virtual Try-On
Following the approach from ViTON and OpenPose
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw
import mediapipe as mp
import logging
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)

class PoseEstimator:
    """Pose estimation using MediaPipe with ViTON-style keypoint mapping"""
    
    def __init__(self):
        """Initialize pose estimator"""
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize pose detection
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # OpenPose-style keypoint mapping (25 keypoints)
        # MediaPipe has 33 landmarks, we map them to OpenPose format
        self.mediapipe_to_openpose = {
            0: 0,   # nose -> nose
            11: 1,  # left_shoulder -> neck (approximated)
            12: 1,  # right_shoulder -> neck (approximated) 
            12: 2,  # right_shoulder -> right_shoulder
            14: 3,  # right_elbow -> right_elbow
            16: 4,  # right_wrist -> right_wrist
            11: 5,  # left_shoulder -> left_shoulder
            13: 6,  # left_elbow -> left_elbow
            15: 7,  # left_wrist -> left_wrist
            24: 8,  # right_hip -> right_hip
            26: 9,  # right_knee -> right_knee
            28: 10, # right_ankle -> right_ankle
            23: 11, # left_hip -> left_hip
            25: 12, # left_knee -> left_knee
            27: 13, # left_ankle -> left_ankle
            5: 14,  # right_eye -> right_eye
            2: 15,  # left_eye -> left_eye
            8: 16,  # right_ear -> right_ear
            7: 17,  # left_ear -> left_ear
        }
        
        logger.info("PoseEstimator initialized successfully")
    
    def estimate_pose(self, image: Image.Image) -> Optional[Dict]:
        """
        Estimate pose from image
        
        Args:
            image: PIL Image
            
        Returns:
            Dictionary containing pose information in OpenPose format
        """
        try:
            # Convert PIL to OpenCV
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
            
            # Run pose estimation
            results = self.pose.process(image_rgb)
            
            if not results.pose_landmarks:
                logger.warning("No pose landmarks detected")
                return None
            
            # Extract keypoints in OpenPose format
            keypoints = self._extract_openpose_keypoints(results.pose_landmarks, image.size)
            
            # Create pose map
            pose_map = self._create_pose_map(keypoints, image.size)
            
            # Create body segmentation mask
            body_mask = None
            if results.segmentation_mask is not None:
                mask_array = (results.segmentation_mask > 0.5).astype(np.uint8) * 255
                body_mask = Image.fromarray(mask_array, mode='L')
                body_mask = body_mask.resize(image.size, Image.Resampling.LANCZOS)
            
            return {
                'keypoints': keypoints,
                'pose_map': pose_map,
                'body_mask': body_mask,
                'confidence': self._calculate_pose_confidence(keypoints)
            }
            
        except Exception as e:
            logger.error(f"Error in pose estimation: {str(e)}")
            return None
    
    def _extract_openpose_keypoints(self, landmarks, image_size: Tuple[int, int]) -> List[List[float]]:
        """Extract keypoints in OpenPose format (25 keypoints)"""
        try:
            width, height = image_size
            
            # Initialize 25 keypoints (OpenPose format)
            keypoints = [[0.0, 0.0, 0.0] for _ in range(25)]
            
            # MediaPipe landmarks to array
            mp_landmarks = []
            for landmark in landmarks.landmark:
                mp_landmarks.append([
                    landmark.x * width,
                    landmark.y * height,
                    landmark.visibility
                ])
            
            # Map MediaPipe to OpenPose keypoints
            # Key body points for virtual try-on
            if len(mp_landmarks) >= 33:
                # 0: Nose
                keypoints[0] = mp_landmarks[0]
                
                # 1: Neck (midpoint of shoulders)
                if mp_landmarks[11][2] > 0.5 and mp_landmarks[12][2] > 0.5:
                    keypoints[1] = [
                        (mp_landmarks[11][0] + mp_landmarks[12][0]) / 2,
                        (mp_landmarks[11][1] + mp_landmarks[12][1]) / 2,
                        min(mp_landmarks[11][2], mp_landmarks[12][2])
                    ]
                
                # 2: Right Shoulder
                keypoints[2] = mp_landmarks[12]
                
                # 3: Right Elbow
                keypoints[3] = mp_landmarks[14]
                
                # 4: Right Wrist
                keypoints[4] = mp_landmarks[16]
                
                # 5: Left Shoulder
                keypoints[5] = mp_landmarks[11]
                
                # 6: Left Elbow
                keypoints[6] = mp_landmarks[13]
                
                # 7: Left Wrist
                keypoints[7] = mp_landmarks[15]
                
                # 8: Mid Hip (midpoint of hips)
                if mp_landmarks[23][2] > 0.5 and mp_landmarks[24][2] > 0.5:
                    keypoints[8] = [
                        (mp_landmarks[23][0] + mp_landmarks[24][0]) / 2,
                        (mp_landmarks[23][1] + mp_landmarks[24][1]) / 2,
                        min(mp_landmarks[23][2], mp_landmarks[24][2])
                    ]
                
                # 9: Right Hip
                keypoints[9] = mp_landmarks[24]
                
                # 10: Right Knee
                keypoints[10] = mp_landmarks[26]
                
                # 11: Right Ankle
                keypoints[11] = mp_landmarks[28]
                
                # 12: Left Hip
                keypoints[12] = mp_landmarks[23]
                
                # 13: Left Knee
                keypoints[13] = mp_landmarks[25]
                
                # 14: Left Ankle
                keypoints[14] = mp_landmarks[27]
                
                # 15: Right Eye
                keypoints[15] = mp_landmarks[5]
                
                # 16: Left Eye
                keypoints[16] = mp_landmarks[2]
                
                # 17: Right Ear
                keypoints[17] = mp_landmarks[8]
                
                # 18: Left Ear
                keypoints[18] = mp_landmarks[7]
                
                # Additional points for better body understanding
                # 19-24: Additional body points (can be interpolated or left as zeros)
            
            return keypoints
            
        except Exception as e:
            logger.error(f"Error extracting OpenPose keypoints: {str(e)}")
            return [[0.0, 0.0, 0.0] for _ in range(25)]
    
    def _create_pose_map(self, keypoints: List[List[float]], image_size: Tuple[int, int]) -> Image.Image:
        """Create pose visualization map"""
        try:
            width, height = image_size
            pose_map = np.zeros((height, width, 3), dtype=np.uint8)
            
            # OpenPose skeleton connections
            connections = [
                # Head
                (15, 0), (16, 0), (17, 15), (18, 16),
                # Body
                (0, 1), (1, 2), (1, 5), (2, 3), (3, 4),
                (5, 6), (6, 7), (1, 8), (8, 9), (8, 12),
                (9, 10), (10, 11), (12, 13), (13, 14)
            ]
            
            # Draw connections
            for connection in connections:
                kp1_idx, kp2_idx = connection
                if (kp1_idx < len(keypoints) and kp2_idx < len(keypoints)):
                    kp1 = keypoints[kp1_idx]
                    kp2 = keypoints[kp2_idx]
                    
                    if kp1[2] > 0.5 and kp2[2] > 0.5:  # visibility check
                        cv2.line(pose_map,
                                (int(kp1[0]), int(kp1[1])),
                                (int(kp2[0]), int(kp2[1])),
                                (255, 255, 255), 2)
            
            # Draw keypoints
            for i, kp in enumerate(keypoints):
                if kp[2] > 0.5:  # visibility check
                    color = (0, 255, 0) if i in [1, 8] else (255, 0, 0)  # Special colors for key points
                    cv2.circle(pose_map, (int(kp[0]), int(kp[1])), 3, color, -1)
            
            return Image.fromarray(pose_map)
            
        except Exception as e:
            logger.error(f"Error creating pose map: {str(e)}")
            return Image.new('RGB', image_size, (0, 0, 0))
    
    def _calculate_pose_confidence(self, keypoints: List[List[float]]) -> float:
        """Calculate overall pose confidence"""
        try:
            visible_keypoints = [kp for kp in keypoints if kp[2] > 0.5]
            if not visible_keypoints:
                return 0.0
            
            total_confidence = sum(kp[2] for kp in visible_keypoints)
            return total_confidence / len(visible_keypoints)
            
        except Exception as e:
            logger.error(f"Error calculating pose confidence: {str(e)}")
            return 0.0
    
    def get_body_regions(self, keypoints: List[List[float]], clothing_category: str) -> Optional[List[Tuple[int, int]]]:
        """Get target body region points for clothing placement"""
        try:
            if clothing_category.lower() in ['tops', 'shirts', 'sweaters', 'hoodies', 'jackets', 'outerwear']:
                # Torso region: shoulders to mid-hip
                left_shoulder = keypoints[5]   # Left shoulder
                right_shoulder = keypoints[2]  # Right shoulder
                mid_hip = keypoints[8]         # Mid hip
                
                if all(kp[2] > 0.5 for kp in [left_shoulder, right_shoulder, mid_hip]):
                    # Create torso quadrilateral
                    shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
                    margin = shoulder_width * 0.1
                    
                    return [
                        (int(left_shoulder[0] - margin), int(left_shoulder[1] - 20)),
                        (int(right_shoulder[0] + margin), int(right_shoulder[1] - 20)),
                        (int(right_shoulder[0] + margin), int(mid_hip[1])),
                        (int(left_shoulder[0] - margin), int(mid_hip[1]))
                    ]
            
            elif clothing_category.lower() in ['bottoms', 'pants', 'jeans', 'shorts']:
                # Legs region: mid-hip to ankles
                left_hip = keypoints[12]    # Left hip
                right_hip = keypoints[9]    # Right hip
                left_ankle = keypoints[14]  # Left ankle
                right_ankle = keypoints[11] # Right ankle
                
                if all(kp[2] > 0.5 for kp in [left_hip, right_hip, left_ankle, right_ankle]):
                    return [
                        (int(left_hip[0]), int(left_hip[1])),
                        (int(right_hip[0]), int(right_hip[1])),
                        (int(right_ankle[0]), int(right_ankle[1])),
                        (int(left_ankle[0]), int(left_ankle[1]))
                    ]
            
            elif clothing_category.lower() in ['dresses']:
                # Full body: shoulders to ankles
                left_shoulder = keypoints[5]
                right_shoulder = keypoints[2]
                left_ankle = keypoints[14]
                right_ankle = keypoints[11]
                
                if all(kp[2] > 0.5 for kp in [left_shoulder, right_shoulder, left_ankle, right_ankle]):
                    shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
                    margin = shoulder_width * 0.2
                    
                    return [
                        (int(left_shoulder[0] - margin), int(left_shoulder[1] - 20)),
                        (int(right_shoulder[0] + margin), int(right_shoulder[1] - 20)),
                        (int(right_ankle[0] + margin), int(right_ankle[1])),
                        (int(left_ankle[0] - margin), int(left_ankle[1]))
                    ]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting body regions: {str(e)}")
            return None

# Create singleton instance
pose_estimator = PoseEstimator()
