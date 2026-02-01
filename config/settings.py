"""
Application settings and configuration management
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "Closet App API"
    app_version: str = "1.0.0"
    app_description: str = "Backend API for the Closet App"
    debug: bool = False
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Database (Supabase)
    supabase_url: str
    supabase_service_key: str
    supabase_anon_key: Optional[str] = None
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8081,http://localhost:8082"
    
    # Storage
    storage_bucket: str = "clothing-image"
    profile_pictures_bucket: str = "profile-picture"
    digital_twin_bucket: str = "digital-twin"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_image_types: str = "image/jpeg,image/png,image/webp"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    
    # API
    api_v1_prefix: str = "/api/v1"
    backend_url: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Monitoring
    enable_metrics: bool = True
    enable_health_checks: bool = True
    
    @field_validator("supabase_url", "supabase_service_key", "supabase_anon_key", mode="after")
    @classmethod
    def strip_whitespace(cls, v):
        if v is None:
            return v
        return v.strip() if isinstance(v, str) else v
    
    @field_validator("allowed_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return []
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get allowed origins as a list"""
        return self.parse_cors_origins(self.allowed_origins)
    
    @field_validator("allowed_image_types", mode="after")
    @classmethod
    def parse_image_types(cls, v):
        if v is None or v == "":
            return ["image/jpeg", "image/png", "image/webp"]
        if isinstance(v, str):
            return [img_type.strip() for img_type in v.split(",") if img_type.strip()]
        if isinstance(v, list):
            return v
        return ["image/jpeg", "image/png", "image/webp"]
    
    @property
    def allowed_image_types_list(self) -> List[str]:
        """Get allowed image types as a list"""
        return self.parse_image_types(self.allowed_image_types)
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of: {allowed_envs}")
        return v
    
    @field_validator("debug")
    @classmethod
    def validate_debug(cls, v, info):
        if info.data.get("environment") == "production" and v:
            return False  # Force debug=False in production
        return v
    
    @field_validator('*', mode='before')
    @classmethod
    def strip_strings(cls, v):
        """Strip whitespace from all string fields"""
        if isinstance(v, str):
            return v.strip()
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra environment variables
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


# Environment-specific settings
def get_environment_settings() -> Settings:
    """Get settings based on current environment"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return get_production_settings()
    elif env == "staging":
        return get_staging_settings()
    else:
        return get_development_settings()


def get_development_settings() -> Settings:
    """Development environment settings"""
    return Settings(
        environment="development",
        debug=True,
        reload=True,
        log_level="DEBUG",
        allowed_origins=[
            "http://localhost:3000",
            "http://localhost:8081",
            "http://localhost:8082",
            "exp://192.168.1.169:8082",
            "exp://192.168.1.100:8081",
            "exp://192.168.1.157:8082",
            "http://192.168.1.157:8082",
        ]
    )


def get_staging_settings() -> Settings:
    """Staging environment settings"""
    return Settings(
        environment="staging",
        debug=False,
        reload=False,
        log_level="INFO",
        allowed_origins=[
            "https://staging.yourdomain.com",
            "https://*.vercel.app",
        ]
    )


def get_production_settings() -> Settings:
    """Production environment settings"""
    return Settings(
        environment="production",
        debug=False,
        reload=False,
        log_level="WARNING",
        allowed_origins=[
            "https://yourdomain.com",
            "https://*.vercel.app",
            "https://*.vercel.com",
        ]
    )
