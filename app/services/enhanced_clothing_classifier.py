"""
Enhanced clothing classification service with season detection
Extends the base classifier to include seasonal analysis
"""
import base64
import io
import logging
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

TF_AVAILABLE = False
tf = None


class EnhancedClothingClassifier:
    """Enhanced classifier for clothing items with season detection"""
    
    # Season mapping based on clothing characteristics
    SEASON_MAPPING = {
        'spring': {
            'colors': ['light', 'pastel', 'bright'],
            'materials': ['cotton', 'linen', 'light'],
            'items': ['light_jacket', 'cardigan', 'light_dress', 'sneakers'],
            'weight': 'light'
        },
        'summer': {
            'colors': ['bright', 'white', 'light', 'vibrant'],
            'materials': ['cotton', 'linen', 'silk', 'light'],
            'items': ['shorts', 'tank_top', 'sundress', 'sandals', 'flip_flops'],
            'weight': 'very_light'
        },
        'fall': {
            'colors': ['warm', 'earth', 'orange', 'brown', 'burgundy'],
            'materials': ['wool', 'flannel', 'denim', 'leather'],
            'items': ['sweater', 'jacket', 'boots', 'jeans', 'scarf'],
            'weight': 'medium'
        },
        'winter': {
            'colors': ['dark', 'black', 'navy', 'gray', 'white'],
            'materials': ['wool', 'cashmere', 'down', 'fleece', 'leather'],
            'items': ['coat', 'sweater', 'boots', 'gloves', 'hat', 'scarf'],
            'weight': 'heavy'
        }
    }
    
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
        """Initialize the enhanced clothing classifier"""
        self.model = None
        self.image_size = (299, 299)

        if model_path and os.path.exists(model_path):
            global TF_AVAILABLE, tf
            if not TF_AVAILABLE:
                try:
                    import tensorflow as _tf
                    tf = _tf
                    TF_AVAILABLE = True
                except Exception as e:
                    logger.warning(f"TensorFlow not available: {e}")
            if TF_AVAILABLE:
                try:
                    self.model = tf.keras.models.load_model(model_path)
                    logger.info(f"Enhanced clothing classifier model loaded from {model_path}")
                except Exception as e:
                    logger.error(f"Failed to load model: {e}")
                    self.model = None
    
    def is_configured(self) -> bool:
        """Check if classifier is ready"""
        return TF_AVAILABLE and self.model is not None
    
    def analyze_season_from_image(self, image: Image.Image) -> Dict[str, float]:
        """
        Analyze image characteristics to determine seasonal suitability
        Returns confidence scores for each season
        """
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get image characteristics
            img_array = np.array(image)
            
            # Analyze color palette
            colors = self._analyze_colors(img_array)
            
            # Analyze texture/material (basic heuristic)
            texture = self._analyze_texture(img_array)
            
            # Analyze shape/silhouette
            shape = self._analyze_shape(img_array)
            
            # Calculate season scores
            season_scores = {}
            
            for season, characteristics in self.SEASON_MAPPING.items():
                score = 0.0
                
                # Color analysis
                color_score = self._calculate_color_score(colors, characteristics['colors'])
                score += color_score * 0.4
                
                # Texture analysis
                texture_score = self._calculate_texture_score(texture, characteristics['materials'])
                score += texture_score * 0.3
                
                # Shape analysis
                shape_score = self._calculate_shape_score(shape, characteristics['items'])
                score += shape_score * 0.3
                
                season_scores[season] = min(score, 1.0)
            
            return season_scores
            
        except Exception as e:
            logger.error(f"Error analyzing season from image: {str(e)}")
            return {'spring': 0.25, 'summer': 0.25, 'fall': 0.25, 'winter': 0.25}
    
    def _analyze_colors(self, img_array: np.ndarray) -> Dict[str, float]:
        """Analyze color characteristics of the image"""
        # Calculate average color
        avg_color = np.mean(img_array, axis=(0, 1))
        
        # Calculate color brightness
        brightness = np.mean(avg_color) / 255.0
        
        # Calculate color saturation
        max_color = np.max(avg_color)
        min_color = np.min(avg_color)
        saturation = (max_color - min_color) / 255.0 if max_color > 0 else 0
        
        # Determine dominant color family
        dominant_color = 'neutral'
        if avg_color[0] > avg_color[1] and avg_color[0] > avg_color[2]:
            dominant_color = 'warm' if avg_color[0] > 150 else 'earth'
        elif avg_color[1] > avg_color[2]:
            dominant_color = 'bright'
        elif avg_color[2] > avg_color[0] and avg_color[2] > avg_color[1]:
            dominant_color = 'cool'
        
        return {
            'brightness': brightness,
            'saturation': saturation,
            'dominant_color': dominant_color,
            'avg_rgb': avg_color.tolist()
        }
    
    def _analyze_texture(self, img_array: np.ndarray) -> Dict[str, float]:
        """Analyze texture characteristics (basic heuristic)"""
        # Convert to grayscale for texture analysis
        gray = np.mean(img_array, axis=2)
        
        # Calculate texture variance (roughness)
        texture_variance = np.var(gray)
        
        # Calculate edge density (smoothness)
        edges_h = np.abs(np.diff(gray, axis=0))
        edges_v = np.abs(np.diff(gray, axis=1))
        # Pad to match dimensions
        min_h, min_w = min(edges_h.shape[0], edges_v.shape[0]), min(edges_h.shape[1], edges_v.shape[1])
        edges = edges_h[:min_h, :min_w] + edges_v[:min_h, :min_w]
        edge_density = np.mean(edges)
        
        # Determine texture type
        if texture_variance > 1000:
            texture_type = 'rough'
        elif texture_variance < 200:
            texture_type = 'smooth'
        else:
            texture_type = 'medium'
        
        return {
            'variance': texture_variance,
            'edge_density': edge_density,
            'type': texture_type
        }
    
    def _analyze_shape(self, img_array: np.ndarray) -> Dict[str, float]:
        """Analyze shape characteristics"""
        # Calculate aspect ratio
        height, width = img_array.shape[:2]
        aspect_ratio = width / height
        
        # Calculate area coverage (how much of the image is occupied)
        # This is a simplified heuristic
        non_white_pixels = np.sum(np.any(img_array < 240, axis=2))
        total_pixels = img_array.shape[0] * img_array.shape[1]
        coverage = non_white_pixels / total_pixels
        
        return {
            'aspect_ratio': aspect_ratio,
            'coverage': coverage
        }
    
    def _calculate_color_score(self, colors: Dict, season_colors: List[str]) -> float:
        """Calculate color score for season"""
        score = 0.0
        
        # Brightness analysis
        if 'light' in season_colors and colors['brightness'] > 0.6:
            score += 0.3
        elif 'dark' in season_colors and colors['brightness'] < 0.4:
            score += 0.3
        
        # Saturation analysis
        if 'bright' in season_colors and colors['saturation'] > 0.5:
            score += 0.3
        elif 'pastel' in season_colors and colors['saturation'] < 0.4:
            score += 0.3
        
        # Dominant color analysis
        if colors['dominant_color'] in season_colors:
            score += 0.4
        
        return min(score, 1.0)
    
    def _calculate_texture_score(self, texture: Dict, season_materials: List[str]) -> float:
        """Calculate texture score for season"""
        score = 0.0
        
        # Texture type analysis
        if texture['type'] == 'smooth' and 'silk' in season_materials:
            score += 0.4
        elif texture['type'] == 'rough' and 'wool' in season_materials:
            score += 0.4
        elif texture['type'] == 'medium':
            score += 0.2
        
        # Edge density analysis
        if texture['edge_density'] < 10 and 'light' in season_materials:
            score += 0.3
        elif texture['edge_density'] > 20 and 'heavy' in season_materials:
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_shape_score(self, shape: Dict, season_items: List[str]) -> float:
        """Calculate shape score for season"""
        score = 0.0
        
        # Aspect ratio analysis
        if shape['aspect_ratio'] > 1.5:  # Wide items (like shorts)
            if 'shorts' in season_items:
                score += 0.4
        elif shape['aspect_ratio'] < 0.8:  # Tall items (like dresses)
            if 'dress' in season_items:
                score += 0.4
        
        # Coverage analysis
        if shape['coverage'] > 0.8:  # Heavy coverage
            if 'coat' in season_items or 'sweater' in season_items:
                score += 0.3
        elif shape['coverage'] < 0.5:  # Light coverage
            if 'tank' in season_items or 'shorts' in season_items:
                score += 0.3
        
        return min(score, 1.0)
    
    def classify_with_season(self, base64_image: str) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict], Optional[Dict]]:
        """
        Enhanced classification that includes both category and season detection
        
        Returns: (success, predicted_category, ml_label, confidence_scores, season_scores)
        """
        try:
            if not self.is_configured():
                logger.info("Using fallback classification (no ML model)")
                return self._fallback_classification_with_season(base64_image)
            
            logger.info("Enhanced classification: category + season detection")
            
            # Decode and load image
            image_data = base64.b64decode(base64_image)
            img = Image.open(io.BytesIO(image_data))
            
            # Resize to model input size
            img_resized = img.resize(self.image_size)
            
            # Convert to RGB if needed
            if img_resized.mode != 'RGB':
                img_resized = img_resized.convert('RGB')
            
            # Prepare for model
            x = np.array(img_resized)
            X = np.array([x])
            X = tf.keras.applications.xception.preprocess_input(X)
            
            # Get category prediction
            predictions = self.model.predict(X, verbose=0)
            predicted_class = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class])
            
            # Get category results
            ml_label = self.ML_LABELS.get(predicted_class, 'unknown')
            predicted_category = self.CATEGORY_MAPPING.get(ml_label, 'Unknown')
            
            # Get season analysis
            season_scores = self.analyze_season_from_image(img)
            
            # Create confidence scores dict
            confidence_scores = {
                'category': confidence,
                'ml_label': ml_label,
                'predicted_class': int(predicted_class)
            }
            
            logger.info(f"Enhanced classification result: {predicted_category} ({ml_label}) - {confidence:.3f}")
            logger.info(f"Season scores: {season_scores}")
            
            return True, predicted_category, ml_label, confidence_scores, season_scores
            
        except Exception as e:
            logger.error(f"Enhanced classification error: {str(e)}")
            return self._fallback_classification_with_season(base64_image)
    
    def _fallback_classification_with_season(self, base64_image: str) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict], Optional[Dict]]:
        """Fallback classification with basic season detection"""
        try:
            # Decode image
            image_data = base64.b64decode(base64_image)
            img = Image.open(io.BytesIO(image_data))
            
            # Basic season analysis
            season_scores = self.analyze_season_from_image(img)
            
            # Simple fallback category
            predicted_category = "Unknown"
            ml_label = "unknown"
            confidence_scores = {
                'category': 0.5,
                'ml_label': 'fallback',
                'predicted_class': -1
            }
            
            logger.info("Using fallback classification with season detection")
            
            return True, predicted_category, ml_label, confidence_scores, season_scores
            
        except Exception as e:
            logger.error(f"Fallback classification error: {str(e)}")
            return False, None, None, None, None
    
    def get_best_season(self, season_scores: Dict[str, float]) -> Tuple[str, float]:
        """Get the best matching season and confidence"""
        if not season_scores:
            return "unknown", 0.0
        
        best_season = max(season_scores.items(), key=lambda x: x[1])
        return best_season[0], best_season[1]
    
    def get_seasonal_recommendations(self, season_scores: Dict[str, float], category: str) -> List[str]:
        """Get seasonal recommendations based on scores and category"""
        recommendations = []
        
        # Get top 2 seasons
        sorted_seasons = sorted(season_scores.items(), key=lambda x: x[1], reverse=True)
        
        for season, score in sorted_seasons[:2]:
            if score > 0.3:  # Only include if confidence is reasonable
                season_info = self.SEASON_MAPPING.get(season, {})
                items = season_info.get('items', [])
                
                # Filter items that match the category
                category_items = [item for item in items if category.lower() in item.lower()]
                if category_items:
                    recommendations.extend(category_items[:2])
        
        return recommendations[:4]  # Limit to 4 recommendations
