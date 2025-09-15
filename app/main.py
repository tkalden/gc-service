"""
Main FastAPI application factory
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings
from app.core.logging import get_logger
from app.core.security import get_security_middleware
from app.core.exceptions import get_exception_handlers
from app.api.v1.router import api_router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )
    
    # Add middleware
    _add_middleware(app, settings)
    
    # Add exception handlers
    _add_exception_handlers(app)
    
    # Add routes
    _add_routes(app, settings)
    
    # Add startup and shutdown events
    _add_events(app)
    
    logger.info(f"Application created for {settings.environment} environment")
    return app


def _add_middleware(app: FastAPI, settings) -> None:
    """Add middleware to the application"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware (production only)
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure with your actual domains
        )
    
    # Security middleware
    for middleware_class in get_security_middleware():
        app.add_middleware(middleware_class)


def _add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to the application"""
    for exception_class, handler in get_exception_handlers().items():
        app.add_exception_handler(exception_class, handler)


def _add_routes(app: FastAPI, settings) -> None:
    """Add routes to the application"""
    
    # Health check endpoint
    @app.get("/")
    async def root():
        return {
            "message": f"{settings.app_name} is running!",
            "version": settings.app_version,
            "environment": settings.environment,
        }
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }
    
    # Include API routes
    app.include_router(api_router, prefix=settings.api_v1_prefix)


def _add_events(app: FastAPI) -> None:
    """Add startup and shutdown events"""
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("Application startup")
        # Add any startup logic here
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutdown")
        # Add any shutdown logic here


# Create the app instance
app = create_app()
