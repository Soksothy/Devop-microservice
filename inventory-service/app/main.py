"""
FastAPI Inventory Microservice
Main application entry point with middleware, exception handlers, and routing.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import inventory
from app.observability import (
    StructuredLogger,
    RequestTracingMiddleware,
    get_prometheus_metrics,
    setup_tracing
)

# Configure structured logging
logger = StructuredLogger.setup_logger(__name__)

# Setup distributed tracing with Jaeger
setup_tracing(service_name="inventory-service", jaeger_host=settings.JAEGER_HOST, jaeger_port=settings.JAEGER_PORT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Inventory Microservice", extra={
        "environment": settings.ENVIRONMENT,
        "database": settings.DATABASE_NAME,
        "trace_id": "startup"
    })
    
    try:
        await connect_to_mongo()
        logger.info("Application startup complete", extra={"trace_id": "startup"})
    except Exception as e:
        logger.error(f"Failed to start application: {e}", extra={"trace_id": "startup"})
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Inventory Microservice", extra={"trace_id": "shutdown"})
    await close_mongo_connection()
    logger.info("Application shutdown complete", extra={"trace_id": "shutdown"})


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready inventory management microservice with full observability",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)


# Middlewares
app.add_middleware(RequestTracingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Observability endpoints
@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint."""
    return await get_prometheus_metrics()


@app.get("/health/live", tags=["Health"])
async def liveness():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
async def readiness():
    """Kubernetes readiness probe with DB check."""
    from app.database import get_database
    try:
        db = await get_database()
        await db.command("ping")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "disconnected"}
        )


# Exception handlers
@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server errors."""
    trace_id = getattr(request.scope, "trace_id", "unknown")
    logger.error(f"Internal server error: {exc}", extra={"trace_id": trace_id}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error - please try again later",
            "code": "INTERNAL_ERROR",
            "trace_id": trace_id
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    trace_id = getattr(request.scope, "trace_id", "unknown")
    logger.error(f"Unhandled exception: {exc}", extra={"trace_id": trace_id}, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "code": "UNEXPECTED_ERROR",
            "trace_id": trace_id
        }
    )


# Include routers
app.include_router(inventory.router, prefix=settings.API_V1_PREFIX, tags=["Inventory"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "metrics": "/metrics",
        "health": {
            "liveness": "/health/live",
            "readiness": "/health/ready"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
