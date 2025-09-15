"""
Logging configuration for the application
"""

import logging
import logging.config
import sys
from typing import Dict, Any
from config.settings import get_settings


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration based on environment"""
    settings = get_settings()
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "default" if settings.environment != "production" else "json",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "app": {
                "level": settings.log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }
    
    # Add file handlers only in non-production environments
    if settings.environment != "production":
        config["loggers"]["app"]["handlers"] = ["console", "file"]
        config["loggers"]["uvicorn.error"]["handlers"] = ["console", "error_file"]
    else:
        # In production, use only console logging (no file handlers)
        config["loggers"]["app"]["handlers"] = ["console"]
        config["loggers"]["uvicorn.error"]["handlers"] = ["console"]
        # Remove file handlers from config in production
        config["handlers"] = {k: v for k, v in config["handlers"].items() if "file" not in k}
    
    return config


def setup_logging() -> None:
    """Setup application logging"""
    import os
    
    # Only create logs directory in non-production environments
    # Vercel serverless environment has read-only file system
    if get_settings().environment != "production":
        try:
            os.makedirs("logs", exist_ok=True)
        except OSError:
            # If we can't create logs directory, continue without file logging
            pass
    
    # Configure logging
    logging.config.dictConfig(get_logging_config())
    
    # Get logger
    logger = logging.getLogger("app")
    logger.info(f"Logging configured for {get_settings().environment} environment")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(f"app.{name}")


# Initialize logging when module is imported
setup_logging()
