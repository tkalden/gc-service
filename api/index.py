"""
Vercel serverless function entry point for FastAPI app
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="Closet App API",
    description="Backend API for the Closet App",
    version="1.0.0",
    debug=False,
    docs_url=None,
    redoc_url=None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Closet App API is running", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "closet-app-api"}

# Export for Vercel
handler = app
