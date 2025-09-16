"""
Main FastAPI application for Vercel deployment
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from config.settings import get_settings
from app.core.logging import get_logger
from app.core.security import get_security_middleware
from app.core.exceptions import get_exception_handlers
from app.api.v1.router import api_router

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Closet App API",
    description="Backend API for the Closet App",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Get settings
settings = get_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware (production only)
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )

# Add security middleware
for middleware_class in get_security_middleware():
    app.add_middleware(middleware_class)

# Add exception handlers
for exception_class, handler in get_exception_handlers().items():
    app.add_exception_handler(exception_class, handler)

# Health check endpoints
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

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")

# Export the app for Vercel
handler = app
