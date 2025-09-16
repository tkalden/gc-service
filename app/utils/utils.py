"""
Basic utility functions for the Closet App
AI-specific utilities are in ai_models/utils.py
"""

import os
import base64
from typing import Optional
from PIL import Image
import io


def image_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """Convert PIL Image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str


def base64_to_image(base64_str: str) -> Image.Image:
    """Convert base64 string to PIL Image"""
    img_data = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(img_data))


def ensure_directory_exists(directory: str) -> None:
    """Ensure a directory exists, create if it doesn't"""
    os.makedirs(directory, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()


def is_valid_image_format(filename: str) -> bool:
    """Check if file has a valid image format"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
    return get_file_extension(filename) in valid_extensions
