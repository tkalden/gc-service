"""
Development environment configuration
"""

from ..settings import Settings


def get_development_config() -> Settings:
    """Get development environment configuration"""
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
        ],
        rate_limit_requests=1000,  # More lenient for development
        enable_metrics=True,
        enable_health_checks=True,
    )
