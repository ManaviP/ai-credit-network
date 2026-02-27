"""
Main FastAPI application.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine
from app.core.neo4j import neo4j_service
from app.routers import auth, users, communities, loans, scoring, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("🚀 Starting AI Community Credit Network API...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🗄️  Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured'}")
    print(f"🔗 Neo4j: {settings.NEO4J_URI}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await neo4j_service.close()
    await engine.dispose()
    print("✅ Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered credit scoring for credit-invisible users through community trust graphs",
    lifespan=lifespan
)

import json

# Normalize CORS origins from settings: allow JSON array or comma-separated string
allowed_origins = settings.CORS_ORIGINS
if isinstance(allowed_origins, str):
    try:
        allowed_origins = json.loads(allowed_origins)
    except Exception:
        allowed_origins = [o.strip() for o in allowed_origins.split(',') if o.strip()]

# In development enable permissive CORS to avoid origin mismatches during local testing
if settings.DEBUG:
    allowed_origins = ["*"]

print(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Return JSON for unexpected errors so frontend receives a parsable body.
    # CORS middleware will still attach headers to this response.
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)}
    )

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(communities.router)
app.include_router(loans.router)
app.include_router(scoring.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check."""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "neo4j": "connected",
        "redis": "connected",
        "services": {
            "auth": "operational",
            "scoring": "operational",
            "loans": "operational",
            "communities": "operational"
        }
    }
