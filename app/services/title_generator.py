"""
Title generation service for clothing items
"""
import logging
from typing import Optional, Dict, List
import random

logger = logging.getLogger(__name__)


class TitleGenerator:
    """Generate descriptive titles for clothing items"""
    
    # Title templates based on category and season
    TITLE_TEMPLATES = {
        'Tops': {
            'spring': [
                "Light {color} {material} {type}",
                "Spring {color} {type}",
                "Fresh {color} {material} {type}",
                "Bright {color} {type} for Spring"
            ],
            'summer': [
                "Cool {color} {type}",
                "Summer {color} {material} {type}",
                "Light {color} {type}",
                "Breezy {color} {type}"
            ],
            'fall': [
                "Warm {color} {material} {type}",
                "Cozy {color} {type}",
                "Autumn {color} {type}",
                "Rich {color} {material} {type}"
            ],
            'winter': [
                "Warm {color} {material} {type}",
                "Winter {color} {type}",
                "Thick {color} {material} {type}",
                "Insulated {color} {type}"
            ]
        },
        'Bottoms': {
            'spring': [
                "Light {color} {material} {type}",
                "Spring {color} {type}",
                "Fresh {color} {type}",
                "Comfortable {color} {type}"
            ],
            'summer': [
                "Cool {color} {type}",
                "Summer {color} {type}",
                "Light {color} {material} {type}",
                "Casual {color} {type}"
            ],
            'fall': [
                "Warm {color} {material} {type}",
                "Cozy {color} {type}",
                "Autumn {color} {type}",
                "Durable {color} {type}"
            ],
            'winter': [
                "Warm {color} {material} {type}",
                "Winter {color} {type}",
                "Thick {color} {material} {type}",
                "Insulated {color} {type}"
            ]
        },
        'Dresses': {
            'spring': [
                "Elegant {color} {material} {type}",
                "Spring {color} {type}",
                "Feminine {color} {type}",
                "Graceful {color} {type}"
            ],
            'summer': [
                "Light {color} {type}",
                "Summer {color} {type}",
                "Breezy {color} {type}",
                "Casual {color} {type}"
            ],
            'fall': [
                "Warm {color} {material} {type}",
                "Autumn {color} {type}",
                "Cozy {color} {type}",
                "Elegant {color} {type}"
            ],
            'winter': [
                "Warm {color} {material} {type}",
                "Winter {color} {type}",
                "Thick {color} {type}",
                "Insulated {color} {type}"
            ]
        },
        'Outerwear': {
            'spring': [
                "Light {color} {material} {type}",
                "Spring {color} {type}",
                "Versatile {color} {type}",
                "Stylish {color} {type}"
            ],
            'summer': [
                "Light {color} {type}",
                "Summer {color} {type}",
                "Breathable {color} {type}",
                "Casual {color} {type}"
            ],
            'fall': [
                "Warm {color} {material} {type}",
                "Autumn {color} {type}",
                "Cozy {color} {type}",
                "Durable {color} {type}"
            ],
            'winter': [
                "Warm {color} {material} {type}",
                "Winter {color} {type}",
                "Thick {color} {type}",
                "Insulated {color} {type}"
            ]
        },
        'Shoes': {
            'spring': [
                "Comfortable {color} {type}",
                "Spring {color} {type}",
                "Versatile {color} {type}",
                "Stylish {color} {type}"
            ],
            'summer': [
                "Light {color} {type}",
                "Summer {color} {type}",
                "Breathable {color} {type}",
                "Casual {color} {type}"
            ],
            'fall': [
                "Durable {color} {type}",
                "Autumn {color} {type}",
                "Sturdy {color} {type}",
                "Weather-resistant {color} {type}"
            ],
            'winter': [
                "Warm {color} {type}",
                "Winter {color} {type}",
                "Insulated {color} {type}",
                "Weatherproof {color} {type}"
            ]
        },
        'Accessories': {
            'spring': [
                "Stylish {color} {type}",
                "Spring {color} {type}",
                "Elegant {color} {type}",
                "Fashionable {color} {type}"
            ],
            'summer': [
                "Light {color} {type}",
                "Summer {color} {type}",
                "Casual {color} {type}",
                "Trendy {color} {type}"
            ],
            'fall': [
                "Warm {color} {type}",
                "Autumn {color} {type}",
                "Cozy {color} {type}",
                "Stylish {color} {type}"
            ],
            'winter': [
                "Warm {color} {type}",
                "Winter {color} {type}",
                "Insulated {color} {type}",
                "Protective {color} {type}"
            ]
        }
    }
    
    # Color variations
    COLOR_VARIATIONS = {
        'red': ['crimson', 'burgundy', 'maroon', 'scarlet', 'cherry'],
        'blue': ['navy', 'royal', 'sky', 'teal', 'azure'],
        'green': ['forest', 'emerald', 'mint', 'olive', 'sage'],
        'yellow': ['gold', 'amber', 'lemon', 'mustard', 'cream'],
        'purple': ['violet', 'lavender', 'plum', 'mauve', 'lilac'],
        'pink': ['rose', 'coral', 'salmon', 'peach', 'blush'],
        'orange': ['tangerine', 'apricot', 'peach', 'coral', 'amber'],
        'brown': ['chocolate', 'coffee', 'tan', 'beige', 'caramel'],
        'black': ['charcoal', 'ebony', 'onyx', 'jet', 'midnight'],
        'white': ['ivory', 'cream', 'pearl', 'snow', 'chalk'],
        'gray': ['silver', 'ash', 'slate', 'steel', 'pewter']
    }
    
    # Material variations
    MATERIAL_VARIATIONS = {
        'cotton': ['cotton blend', 'organic cotton', 'soft cotton'],
        'wool': ['merino wool', 'cashmere', 'alpaca wool'],
        'silk': ['pure silk', 'silk blend', 'satin'],
        'denim': ['denim', 'stretch denim', 'raw denim'],
        'leather': ['genuine leather', 'suede', 'patent leather'],
        'polyester': ['polyester blend', 'performance fabric'],
        'linen': ['linen', 'linen blend', 'breathable linen']
    }
    
    def __init__(self):
        """Initialize the title generator"""
        logger.info("Title generator initialized")
    
    def generate_title(self, category: str, season: str, ml_label: str, 
                      color_hint: Optional[str] = None, 
                      material_hint: Optional[str] = None) -> str:
        """
        Generate a descriptive title for a clothing item
        
        Args:
            category: Clothing category (Tops, Bottoms, etc.)
            season: Detected season (spring, summer, fall, winter)
            ml_label: ML model label (t-shirt, dress, etc.)
            color_hint: Optional color hint from image analysis
            material_hint: Optional material hint from image analysis
        
        Returns:
            Generated title string
        """
        try:
            # Get templates for category and season
            templates = self.TITLE_TEMPLATES.get(category, {}).get(season, [])
            
            if not templates:
                # Fallback to generic templates
                templates = [
                    f"{{color}} {{material}} {{type}}",
                    f"Stylish {{color}} {{type}}",
                    f"Fashionable {{color}} {{type}}"
                ]
            
            # Select random template
            template = random.choice(templates)
            
            # Generate attributes
            color = self._generate_color(color_hint)
            material = self._generate_material(material_hint, season)
            item_type = self._generate_item_type(ml_label, category)
            
            # Format the title
            title = template.format(
                color=color,
                material=material,
                type=item_type
            )
            
            # Clean up the title
            title = self._clean_title(title)
            
            logger.info(f"Generated title: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            # Fallback title
            return f"Stylish {category.lower()}"
    
    def _generate_color(self, color_hint: Optional[str] = None) -> str:
        """Generate a color name"""
        if color_hint:
            # Use color hint if available
            variations = self.COLOR_VARIATIONS.get(color_hint.lower(), [color_hint])
            return random.choice(variations)
        
        # Random color
        colors = list(self.COLOR_VARIATIONS.keys())
        base_color = random.choice(colors)
        variations = self.COLOR_VARIATIONS[base_color]
        return random.choice(variations)
    
    def _generate_material(self, material_hint: Optional[str] = None, season: str = None) -> str:
        """Generate a material name"""
        if material_hint:
            # Use material hint if available
            variations = self.MATERIAL_VARIATIONS.get(material_hint.lower(), [material_hint])
            return random.choice(variations)
        
        # Season-appropriate materials
        seasonal_materials = {
            'spring': ['cotton', 'linen', 'cotton blend'],
            'summer': ['cotton', 'linen', 'silk', 'breathable fabric'],
            'fall': ['wool', 'cotton', 'denim', 'flannel'],
            'winter': ['wool', 'cashmere', 'fleece', 'thick cotton']
        }
        
        materials = seasonal_materials.get(season, ['cotton', 'polyester'])
        base_material = random.choice(materials)
        variations = self.MATERIAL_VARIATIONS.get(base_material, [base_material])
        return random.choice(variations)
    
    def _generate_item_type(self, ml_label: str, category: str) -> str:
        """Generate item type from ML label and category"""
        # Map ML labels to readable types
        type_mapping = {
            't-shirt': 'T-Shirt',
            'shirt': 'Shirt',
            'longsleeve': 'Long Sleeve Shirt',
            'dress': 'Dress',
            'pants': 'Pants',
            'shorts': 'Shorts',
            'skirt': 'Skirt',
            'outwear': 'Jacket',
            'shoes': 'Shoes',
            'hat': 'Hat'
        }
        
        return type_mapping.get(ml_label, category)
    
    def _clean_title(self, title: str) -> str:
        """Clean up the generated title"""
        # Remove extra spaces
        title = ' '.join(title.split())
        
        # Capitalize properly
        title = title.title()
        
        # Fix common issues
        title = title.replace('  ', ' ')
        
        return title
    
    def generate_multiple_titles(self, category: str, season: str, ml_label: str, 
                               count: int = 3) -> List[str]:
        """Generate multiple title options"""
        titles = []
        for _ in range(count):
            title = self.generate_title(category, season, ml_label)
            if title not in titles:
                titles.append(title)
        
        return titles

