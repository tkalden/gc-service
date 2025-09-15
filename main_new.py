"""
Main entry point for the application
"""

from app.main import app

if __name__ == "__main__":
    import uvicorn
    from config.settings import get_settings
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
