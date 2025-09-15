"""
Custom exceptions and error handling
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class ClosetAppException(Exception):
    """Base exception for Closet App"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "CLOSET_APP_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(ClosetAppException):
    """Database operation exception"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "DATABASE_ERROR", details)


class StorageException(ClosetAppException):
    """Storage operation exception"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "STORAGE_ERROR", details)


class AuthenticationException(ClosetAppException):
    """Authentication exception"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class ValidationException(ClosetAppException):
    """Validation exception"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class ServiceUnavailableException(ClosetAppException):
    """Service unavailable exception"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "SERVICE_UNAVAILABLE", details)


class RateLimitException(ClosetAppException):
    """Rate limit exception"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Dict[str, Any] = None):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)


async def closet_app_exception_handler(request: Request, exc: ClosetAppException) -> JSONResponse:
    """Handle ClosetAppException"""
    logger.error(f"ClosetAppException: {exc.message}", extra={
        "error_code": exc.error_code,
        "details": exc.details,
        "path": request.url.path,
        "method": request.method,
    })
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException"""
    logger.warning(f"HTTPException: {exc.detail}", extra={
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method,
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}", extra={
        "path": request.url.path,
        "method": request.method,
    })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors(),
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method,
        "exception_type": type(exc).__name__,
    }, exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
        }
    )


def get_exception_handlers() -> Dict[type, callable]:
    """Get exception handlers for the application"""
    return {
        ClosetAppException: closet_app_exception_handler,
        HTTPException: http_exception_handler,
        StarletteHTTPException: http_exception_handler,
        RequestValidationError: validation_exception_handler,
        Exception: general_exception_handler,
    }
