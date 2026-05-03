"""
Production environment configuration
"""

from ..settings import Settings


def get_production_config() -> Settings:
    """Get production environment configuration"""
    return Settings(
        environment="production",
        debug=False,
        reload=False,
        log_level="WARNING",
        allowed_origins=[
            "https://yourdomain.com",
        ],
        rate_limit_requests=100,  # Stricter for production
        enable_metrics=True,
        enable_health_checks=True,
        # Production-specific settings
        access_token_expire_minutes=15,  # Shorter token lifetime
        refresh_token_expire_days=7,
    )
