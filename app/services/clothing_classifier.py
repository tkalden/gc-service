"""
Clothing classification service using Xception model
"""
import base64
import io
import logging
from typing import Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import TensorFlow
try:
    import tensorflow as tf
    TF_AVAILABLE = True
    logger.info("TensorFlow loaded successfully")
except Exception as e:
    TF_AVAILABLE = False
    logger.warning(f"TensorFlow not available: {str(e)}")


class ClothingClassifier:
    """Classify clothing items using pre-trained Xception model"""
    
    # Category mapping from ML model to app categories
    CATEGORY_MAPPING = {
        'dress': 'Dresses',
        'hat': 'Accessories',
        'longsleeve': 'Tops',
        'outwear': 'Outerwear',
        'pants': 'Bottoms',
        'shirt': 'Tops',
        'shoes': 'Shoes',
        'shorts': 'Bottoms',
        'skirt': 'Bottoms',
        't-shirt': 'Tops'
    }
    
    ML_LABELS = {
        0: 'dress',
        1: 'hat',
        2: 'longsleeve',
        3: 'outwear',
        4: 'pants',
        5: 'shirt',
        6: 'shoes',
        7: 'shorts',
        8: 'skirt',
        9: 't-shirt'
    }
    
    def __init__(self, model_path: str = None):
        """Initialize the clothing classifier"""
        self.model = None
        self.image_size = (299, 299)
        
        if TF_AVAILABLE and model_path:
            try:
                self.model = tf.keras.models.load_model(model_path)
                logger.info(f"Clothing classifier model loaded from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load model: {str(e)}")
                self.model = None
    
    def is_configured(self) -> bool:
        """Check if classifier is ready"""
        return TF_AVAILABLE and self.model is not None
    
    def classify_from_base64(self, base64_image: str) -> Tuple[bool, Optional[str], Optional[str], Optional[dict]]:
        """
        Classify clothing from base64 image
        
        Returns: (success, predicted_category, ml_label, confidence_scores)
        """
        try:
            if not self.is_configured():
                # Fallback: Simple classification based on image analysis
                logger.info("Using fallback classification (no ML model)")
                return self._fallback_classification(base64_image)
            
            logger.info("Classifying clothing from base64 image")
            
            # Decode and load image
            image_data = base64.b64decode(base64_image)
            img = Image.open(io.BytesIO(image_data))
            
            # Resize to model input size
            img = img.resize(self.image_size)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Prepare for model
            x = np.array(img)
            X = np.array([x])
            X = tf.keras.applications.xception.preprocess_input(X)
            
            # Predict
            predictions = self.model.predict(X, verbose=0)
            predicted_idx = predictions[0].argmax()
            confidence = float(predictions[0][predicted_idx])
            
            # Get ML label
            ml_label = self.ML_LABELS[predicted_idx]
            
            # Map to app category
            app_category = self.CATEGORY_MAPPING.get(ml_label, 'Tops')
            
            # Get all confidence scores
            confidence_scores = {
                self.ML_LABELS[i]: float(predictions[0][i]) 
                for i in range(len(predictions[0]))
            }
            
            logger.info(f"Predicted: {ml_label} → {app_category} (confidence: {confidence:.2%})")
            
            return True, app_category, ml_label, {
                'confidence': confidence,
                'ml_label': ml_label,
                'app_category': app_category,
                'all_scores': confidence_scores
            }
            
        except Exception as e:
            error_msg = f"Classification error: {str(e)}"
            logger.error(error_msg)
            # Try fallback classification
            return self._fallback_classification(base64_image)
    
    def _fallback_classification(self, base64_image: str) -> Tuple[bool, str, str, dict]:
        """
        Fallback classification using simple image analysis
        """
        try:
            # Decode and load image
            image_data = base64.b64decode(base64_image)
            img = Image.open(io.BytesIO(image_data))
            
            # Simple heuristics based on image dimensions and colors
            width, height = img.size
            aspect_ratio = width / height
            
            # Convert to RGB for analysis
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get dominant colors
            img_array = np.array(img)
            colors = img_array.reshape(-1, 3)
            
            # Simple classification based on aspect ratio and color analysis
            if aspect_ratio > 1.2:  # Wide image - likely pants or dress
                if np.mean(colors[:, 2]) > 150:  # Bright colors - likely dress
                    category = 'Dresses'
                    ml_label = 'dress'
                else:
                    category = 'Bottoms'
                    ml_label = 'pants'
            elif aspect_ratio < 0.8:  # Tall image - likely shirt or top
                category = 'Tops'
                ml_label = 't-shirt'
            else:  # Square-ish - could be anything
                # Analyze color patterns
                if np.std(colors) > 50:  # High color variation
                    category = 'Tops'
                    ml_label = 'shirt'
                else:
                    category = 'Bottoms'
                    ml_label = 'shorts'
            
            confidence = 0.6  # Moderate confidence for fallback
            
            logger.info(f"Fallback classification: {ml_label} → {category} (confidence: {confidence:.2%})")
            
            return True, category, ml_label, {
                'confidence': confidence,
                'ml_label': ml_label,
                'app_category': category,
                'method': 'fallback_heuristics'
            }
            
        except Exception as e:
            logger.error(f"Fallback classification failed: {str(e)}")
            # Ultimate fallback
            return True, 'Tops', 't-shirt', {
                'confidence': 0.5,
                'ml_label': 't-shirt',
                'app_category': 'Tops',
                'method': 'default_fallback'
            }
    
    def get_status(self) -> dict:
        """Get classifier status"""
        return {
            'available': self.is_configured(),
            'tensorflow_available': TF_AVAILABLE,
            'model_loaded': self.model is not None,
            'image_size': self.image_size,
            'categories': list(self.CATEGORY_MAPPING.values()),
            'ml_labels': list(self.ML_LABELS.values())
        }


# Initialize classifier with model path
# Using local model file in gc-service project
import os

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'clothes_classifier_model.h5')

try:
    clothing_classifier = ClothingClassifier(model_path=MODEL_PATH)
    if not clothing_classifier.is_configured():
        logger.warning("Clothing classifier model not found. Using dummy model.")
except Exception as e:
    logger.warning(f"Could not initialize clothing classifier: {e}")
    clothing_classifier = ClothingClassifier()

