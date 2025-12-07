"""FastAPI main application."""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import deployments, templates

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

app = FastAPI(
    title="Mini-IDP API",
    description="Kubernetes deployment and template management API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(deployments.router)
app.include_router(templates.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Mini-IDP API",
        "version": "0.1.0",
        "description": "Kubernetes deployment and template management API",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

