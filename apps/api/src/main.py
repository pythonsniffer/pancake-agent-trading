from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import get_settings
from .routes import api_router
from .models.database import init_db
from .seed import seed_db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up Pancake Trading Agent API...")
    init_db()
    seed_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down...")


def create_application() -> FastAPI:
    """Create FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI Powered Autonomous Multi-Agent Trading System for PancakeSwap",
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api")

    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.version,
            "status": "running",
            "endpoints": {
                "api": "/api",
                "docs": "/docs",
                "health": "/health"
            }
        }

    @app.get("/health")
    async def health_check():
        from datetime import datetime
        return {
            "status": "healthy",
            "version": settings.version,
            "timestamp": datetime.utcnow().isoformat()
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "message": str(exc)}
        )

    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
