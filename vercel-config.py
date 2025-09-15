"""
Vercel-specific configuration for the Closet App Backend
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Vercel-specific configuration
def get_vercel_config():
    """Get configuration optimized for Vercel deployment"""
    
    # Supabase Configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Validate required environment variables
    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable is required")
    if not supabase_service_key:
        raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")
    
    # Server Configuration for Vercel
    host = "0.0.0.0"  # Vercel requirement
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Get backend URL from Vercel environment or use default
    backend_url = os.getenv("BACKEND_URL") or os.getenv("VERCEL_URL")
    if backend_url and not backend_url.startswith("http"):
        backend_url = f"https://{backend_url}"
    
    # CORS Configuration - include Vercel domains
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    if not allowed_origins or allowed_origins == [""]:
        # Default origins for development and common Vercel domains
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:8081", 
            "http://localhost:8082",
            "https://*.vercel.app",
            "https://*.vercel.com"
        ]
    
    # Storage Configuration
    storage_bucket = "clothing-image"
    profile_pictures_bucket = "profile-picture"
    digital_twin_bucket = "digital-twin"
    max_file_size = 10 * 1024 * 1024  # 10MB
    allowed_image_types = ["image/jpeg", "image/png", "image/webp"]
    
    return {
        "SUPABASE_URL": supabase_url,
        "SUPABASE_SERVICE_KEY": supabase_service_key,
        "HOST": host,
        "PORT": port,
        "DEBUG": debug,
        "BACKEND_URL": backend_url,
        "ALLOWED_ORIGINS": allowed_origins,
        "STORAGE_BUCKET": storage_bucket,
        "PROFILE_PICTURES_BUCKET": profile_pictures_bucket,
        "DIGITAL_TWIN_BUCKET": digital_twin_bucket,
        "MAX_FILE_SIZE": max_file_size,
        "ALLOWED_IMAGE_TYPES": allowed_image_types
    }

# Export configuration
VERCEL_CONFIG = get_vercel_config()
