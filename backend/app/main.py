"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base
from app.routers import projects, datasets, forecasts, events, exclusions, adjustments, diagnostics, insights, auth, sharing, comparison
import os

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",  # Phase 4 - Production Ready
    description="Enterprise-grade forecasting platform with authentication, collaboration, and advanced analytics",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (Phase 1)
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(forecasts.router, prefix="/api/forecasts", tags=["Forecasts"])

# Include routers (Phase 2)
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(exclusions.router, prefix="/api/exclusions", tags=["Exclusions"])
app.include_router(adjustments.router, prefix="/api/adjustments", tags=["Adjustments"])

# Include routers (Phase 3)
app.include_router(diagnostics.router, prefix="/api/diagnostics", tags=["Diagnostics"])
app.include_router(insights.router, prefix="/api/insights", tags=["Insights"])

# Include routers (Phase 4)
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sharing.router, prefix="/api/sharing", tags=["Collaboration"])
app.include_router(comparison.router, prefix="/api/comparison", tags=["Comparison"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "status": "running",
        "docs": "/api/docs",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.app_name}
